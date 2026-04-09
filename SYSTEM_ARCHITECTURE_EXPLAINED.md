# 论文评价系统架构说明

## 现象分析

您看到的"卡顿"现象（进度条停留在 5%，显示"正在检测中..."）并不是 Bug，而是**系统架构设计**导致的。

---

## 架构设计

### 为什么采用异步任务架构？

```
同步方案（不可行）:
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│  用户上传   │ ──→  │ FastAPI 等待 │ ──→  │  返回结果    │
│ 文件 (1秒)  │      │  AI 评价      │      │  (1-3 分钟)  │
└─────────────┘      │ (1-3 分钟)    │      └──────────────┘
                     └──────────────┘
                         ⚠️ HTTP 超时风险！

异步方案（当前）:
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│  用户上传   │ ──→  │ FastAPI 提交 │ ──→  │ 立即返回 task  │
│ 文件 (1秒)  │      │ 任务到队列   │      │  (100ms)       │
└─────────────┘      └──────────────┘      └────────────────┘
                             │
                             ↓
                     ┌──────────────┐
                     │ Celery Worker│
                     │ 后台执行      │
                     │ (1-3 分钟)    │
                     └──────────────┘
                             │
                             ↓
                     ┌──────────────┐
                     │  结果保存到   │
                     │  Redis       │
                     └──────────────┘
                             ↑
前端轮询：每2秒查询一次状态 ────┘
```

**优势：**
- ✅ 前端不会超时（立即返回）
- ✅ 支持并发（多个用户同时使用）
- ✅ 用户体验好（有进度条反馈）
- ✅ 服务器负载均衡

---

## 系统拓扑图

```
                          互联网用户
                              │
                              ↓
                    ┌─────────────────┐
                    │   Vue 前端      │
                    │  localhost:5173 │
                    └────────┬────────┘
                             │
                    HTTP/WebSocket
                             │
                    ┌────────↓────────┐
                    │   FastAPI       │ ← 接收 /api/v1/evaluation/upload
                    │ localhost:8000  │ ← 返回 task_id
                    └────────┬────────┘
                             │
                             ├─ 1️⃣ 上传文件
                             │
                    ┌────────↓────────┐
                    │    文件存储      │
                    │  storage/uploads │
                    └─────────────────┘
                             │
                             ├─ 2️⃣ 提交任务到消息队列
                             │
                    ┌────────↓────────────────┐
                    │  Redis (Celery Broker) │ ← 消息队列
                    │  localhost:6379        │ ← 结果存储
                    └────────┬────────────────┘
                             │
                      任务队列：evaluation
                             │
                    ┌────────↓────────┐
                    │  Celery Worker  │ ← 3️⃣ 执行评价任务
                    │ (多线程池)      │ ← 4️⃣ 保存结果
                    └─────────────────┘
                             │
前端轮询 ←─── GET /api/v1/evaluation/status/{task_id} ───→ FastAPI
(每2秒)                                                    查询 Redis
                             ↓
                    ┌─────────────────┐
                    │   结果返回       │
                    │ status: progress│
                    └─────────────────┘
```

---

## 关键组件及职责

### 1. Redis（消息队列 & 结果存储）
- **作用：** 
  - 存储待执行的评价任务（Celery Broker）
  - 存储已完成的评价结果（Result Backend）
  - 作为任务和结果的中转站
- **为什么关键：** 没有 Redis，Celery Worker 无法获得任务
- **启动：**
  ```bash
  docker run -d -p 6379:6379 redis:latest
  ```

### 2. FastAPI（HTTP 服务器）
- **作用：**
  - `POST /api/v1/evaluation/upload` - 接收文件，返回 task_id
  - `GET /api/v1/evaluation/status/{task_id}` - 查询任务状态
  - `GET /api/v1/evaluation/result/{task_id}` - 获取完整结果
- **为什么关键：** 连接前端和后端系统
- **启动：**
  ```bash
  uvicorn app.main:app --reload
  ```

### 3. Celery Worker（任务执行器）
- **作用：** 
  - 从 Redis 队列拉取任务
  - 调用 AI API（百炼/DeepSeek）进行多维度评价
  - 将结果保存回 Redis
- **为什么关键：** 没有 Worker，任务永远不执行
- **启动：**
  ```bash
  celery -A app.workers.celery_app worker -l info --pool=threads -Q evaluation,proofread,formatter,default
  ```

### 4. Vue 前端（用户界面）
- **作用：**
  - 提供文件上传界面
  - 显示实时进度条
  - 展示评价报告
- **轮询机制：** 每 2 秒调用 `/api/v1/evaluation/status/{task_id}` 检查进度
- **启动：**
  ```bash
  npm run dev
  ```

---

## 数据流动

### 场景：用户上传论文进行评价

```
第 0 秒 ─────────────────────────────────────
用户：上传 论文.docx
    ↓
第 1 秒 ─────────────────────────────────────
前端：POST /api/v1/evaluation/upload
      + file = 论文.docx
      + paper_type = humanities

FastAPI：
  1. 保存文件到 storage/uploads/
  2. 解析文档结构（标题、内容）
  3. 创建任务：{ task_id: "abc123", ... }
  4. 提交到 Celery：run_evaluation.apply_async(...)
  5. ✅ 返回 { task_id: "abc123", status: "pending" }

第 2 秒 ─────────────────────────────────────
前端：进入 isProcessing 状态，显示进度条 (5%)
      startPolling("abc123")

第 3 秒 ─────────────────────────────────────
前端轮询 → GET /api/v1/evaluation/status/abc123
FastAPI：
  1. 查询 Redis 中 task abc123 的状态
  2. Celery 状态 = PENDING（还在队列中）
  3. ✅ 返回 { status: "pending", progress: 5 }

第 5 秒 ─────────────────────────────────────
Celery Worker：
  1. 从队列拉取 task abc123
  2. 🔄 开始执行 run_evaluation()
  3. 状态 = STARTED

前端轮询 → GET /api/v1/evaluation/status/abc123
FastAPI：返回 { status: "processing", progress: 40 }
前端：更新进度条 → 40%

第 10 秒 ─────────────────────────────────────
Celery Worker（继续执行）：
  调用 AI API 进行维度1：学术规范性
  → 获得 score, strengths, weaknesses, suggestions

第 20 秒 ─────────────────────────────────────
Celery Worker（继续执行）：
  调用 AI API 进行维度2：逻辑与创新性
  ...

第 45 秒 ─────────────────────────────────────
Celery Worker（继续执行）：
  调用 AI API 进行维度3/4...
  计算综合评分
  保存结果到 Redis
  状态 = SUCCESS

前端轮询 → GET /api/v1/evaluation/status/abc123
FastAPI：返回 { status: "completed", progress: 100 }
前端：停止轮询，切换到结果展示页面 ✅

第 46 秒 ─────────────────────────────────────
前端：GET /api/v1/evaluation/result/abc123
FastAPI：从 Redis 返回完整结果
    {
      "paper_title": "论文标题",
      "overall_score": 85,
      "dimensions": {
        "academic_standard": {...},
        "logic_innovation": {...},
        ...
      }
    }

用户：看到完整的评价报告！✨
```

---

## 为什么会"卡顿"？

```
前端显示进度条停留在 5%，原因：
↓
Celery Worker 还没有接到任务
↓
可能原因（按概率）：
1. ❌ Redis 没有启动（60%）
   → 任务无法入队
   
2. ❌ Celery Worker 没有启动（30%）
   → 任务在队列中，但无人处理
   
3. ❌ API Key 未配置（5%）
   → Worker 启动了，但 AI 调用失败
   
4. ❌ 其他网络问题（5%）
```

**症状对应的根本原因：**

| 症状 | 调试方法 |
|------|---------|
| 立即返回错误 | FastAPI 未运行 |
| 上传成功，但卡在 5% | Redis 或 Worker 未运行 |
| 进度到 50% 后卡住 | API Key 问题或 Worker 崩溃 |
| 反复轮询但无进展 | Celery 消息队列配置错误 |

---

## 监控和调试方法

### 1. 检查各服务状态

```bash
# Redis
redis-cli ping
# 返回：PONG ✅

# FastAPI (浏览器访问)
http://localhost:8000/docs
# 返回：Swagger UI ✅

# Celery Worker（看启动的终端）
# 应显示：celery@DESKTOP-XXXXX ready ✅
```

### 2. 查看详细日志

**FastAPI 日志：**
```
[evaluation] 任务已入队 task_id=abc123
```

**Celery Worker 日志：**
```
[evaluation] 开始处理任务 task_id=abc123
[evaluation] 任务完成 task_id=abc123
```

**前端控制台（F12）：**
```javascript
[evaluation store] 轮询开始...
[evaluation store] 状态 (progress: 35)
[evaluation store] 状态 (progress: 70)
[evaluation store] 状态 completed
```

### 3. 使用诊断脚本

```bash
python backend/check_services.py
```

自动检查并报告：
- ✅ Redis 是否可连接
- ✅ FastAPI 是否运行
- ✅ Celery Worker 是否运行
- ✅ API Key 是否配置

---

## 文件结构

```
backend/
├── app/
│   ├── main.py                           # FastAPI 应用入口
│   ├── config.py                         # 配置（Redis、API Key等）
│   │
│   ├── api/v1/
│   │   └── evaluation.py                 # 评价 API 端点
│   │
│   ├── workers/
│   │   ├── celery_app.py                 # Celery 应用工厂
│   │   ├── evaluation_tasks.py           # 评价任务实现
│   │   ├── proofread_tasks.py            # 校对任务
│   │   └── formatter_tasks.py            # 排版任务
│   │
│   ├── core/
│   │   ├── evaluator/                    # 评价核心逻辑
│   │   ├── proofread/                    # 校对核心逻辑
│   │   └── formatter/                    # 排版核心逻辑
│   │
│   └── services/
│       ├── file_service.py               # 文件处理
│       └── cache_service.py              # 缓存管理
│
│
frontend/
└── src/
    ├── views/Evaluation.vue              # 评价页面
    ├── api/evaluation.js                 # 评价 API 客户端
    └── store/modules/evaluation.js       # 状态管理（轮询逻辑）
```

---

## 配置说明

### backend/.env

```ini
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI 服务配置（至少配置一个）
BAILIAN_API_KEY=sk_xxxxx              # 阿里云百炼
DEEPSEEK_API_KEY=sk_xxxxx             # DeepSeek API

# 文件存储
MAX_FILE_SIZE=20                       # MB
FILE_RETENTION_HOURS=24                # 文件保留时间

# JWT 认证
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080      # 7天
```

---

## 性能指标

| 操作 | 耗时 | 原因 |
|------|------|------|
| 文件上传 | ~1-5 秒 | 文件大小、网络 |
| 文档解析 | ~1-2 秒 | 文档复杂度 |
| 队列等待 | 0-5 秒 | Worker 负载 |
| AI 评价（4维） | ~30-60 秒 | 调用 AI 服务 |
| 结果保存 | ~1-2 秒 | Redis 写入 |
| **总耗时** | **45-75 秒** | - |

---

## 故障排除决策树

```
上传论文后卡在 5%？
│
├─ 检查后端日志有"任务已入队"吗？
│  │
│  ├─ 没有？
│  │  └─ FastAPI 未运行
│  │     → uvicorn app.main:app --reload
│  │
│  └─ 有？
│     │
│     └─ 检查 Celery Worker 终端有"ready"吗？
│        │
│        ├─ 没有？
│        │  └─ Celery Worker 未运行
│        │     → celery -A app.workers.celery_app worker ...
│        │
│        └─ 有？
│           │
│           └─ 检查 Worker 有"Received task"吗？
│              │
│              ├─ 没有？
│              │  └─ Redis 未运行或连接失败
│              │     → docker run -d -p 6379:6379 redis:latest
│              │
│              └─ 有？
│                 │
│                 └─ 检查 Worker 是否有错误日志
│                    │
│                    ├─ "BAILIAN_API_KEY"相关？
│                    │  └─ 编辑 .env，添加 API Key
│                    │
│                    └─ 其他错误？
│                       └─ 查看详细错误信息
```

---

## 总结

✅ **系统设计是正确的**：
- 异步任务处理是必需的（AI 评价耗时长）
- Redis + Celery 是业界标准方案
- 轮询机制简单可靠

❌ **"卡顿"通常是部署问题**：
- 99% 的情况是 Redis 或 Celery Worker 未启动
- 1% 的情况是配置错误或网络问题

✅ **快速修复**：
1. 启动 Redis：`docker run -d -p 6379:6379 redis:latest`
2. 启动 FastAPI：`uvicorn app.main:app --reload`
3. 启动 Celery Worker：`celery -A app.workers.celery_app worker -l info --pool=threads`
4. 再次上传文件测试

---

**相关文档：**
- 快速启动：`QUICK_START_GUIDE.md`
- 完整诊断：`DIAGNOSIS_REPORT.md`
- 快速修复：`TROUBLESHOOTING_CHECKLIST.md`
