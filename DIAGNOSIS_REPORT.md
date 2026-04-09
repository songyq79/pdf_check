# 论文评价卡顿问题诊断报告

## 问题现象
✗ 上传论文后进度条卡在 5%，显示"正在检测中..."  
✗ 进度条长时间无反应，最终超时  
✗ 浏览器控制台无错误信息，后端无日志输出  

---

## 根本原因

该系统采用 **异步任务架构**：

```
前端上传文件
    ↓
FastAPI 接收 → 立即返回 task_id（不等待结果）
    ↓
将评价任务提交到 Celery 队列（Redis）
    ↓
Celery Worker 从队列拉取任务并执行（后台进行）
    ↓
前端轮询任务状态（每2秒查询一次）
    ↓
当 Celery Worker 完成任务后，结果保存在 Redis
    ↓
前端收到 status=completed，展示结果
```

### ⚠️ 关键依赖
| 组件 | 作用 | 缺失影响 |
|------|------|--------|
| **Redis** | Celery 的消息队列 + 结果存储 | 任务无法入队，永远 PENDING |
| **Celery Worker** | 后台执行评价任务 | 任务不执行，无法完成 |
| **FastAPI** | HTTP API 服务器 | 无法接收/返回请求 |
| **AI API Key** | 调用 AI 服务（百炼/DeepSeek） | 任务执行失败 |

---

## 诊断步骤

### 1. 快速检查
运行诊断脚本（需在后端目录）：
```bash
cd backend
python check_services.py
```

这会检查以下内容：
- ✅ Redis 是否连接
- ✅ Celery 是否配置
- ✅ FastAPI 是否运行
- ✅ API Key 是否配置

### 2. 手动检查

#### 检查 Redis
```bash
redis-cli ping
# 应该返回：PONG
```

#### 检查 FastAPI
```
访问：http://localhost:8000/docs
应该看到 Swagger API 界面
```

#### 检查 Celery Worker
查看启动 Celery 的终端，应该有类似输出：
```
celery@DESKTOP-XXXXX ready.
- concurrency: 4 threads
- pool: threads
[queue] => evaluation, proofread, formatter, default
```

---

## 解决方案

### 必须启动的 3 个服务

#### ① 启动 Redis（必须第一个）

**Windows - Docker 方式（推荐）：**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Windows - Redis for Windows：**
1. 下载：https://github.com/microsoftarchive/redis/releases
2. 双击 `redis-server.exe`

**验证：**
```bash
redis-cli ping
# PONG ✓
```

#### ② 启动 FastAPI

```bash
cd backend

# 激活虚拟环境
venv\Scripts\activate

# 启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验证：**
```
http://localhost:8000/docs （能访问即可）
```

#### ③ 启动 Celery Worker（最重要！）

**在后端目录新开一个终端：**
```bash
cd backend

# 激活虚拟环境
venv\Scripts\activate

# 启动 Worker
celery -A app.workers.celery_app worker \
  -l info \
  --pool=threads \
  -Q evaluation,proofread,formatter,default
```

**关键参数说明：**
| 参数 | 含义 |
|------|------|
| `-A app.workers.celery_app` | 指向 Celery 应用 |
| `-l info` | 日志级别（info=有详细输出） |
| `--pool=threads` | **Windows 必须用 threads 池** |
| `-Q evaluation,...` | 监听的队列 |

**应该看到：**
```
[2026-04-02 14:30:00,000: INFO/MainProcess] celery@DESKTOP ready.
[2026-04-02 14:30:00,000: INFO/MainProcess] - concurrency: 4 threads
[2026-04-02 14:30:00,000: INFO/MainProcess] - pool: threads
[2026-04-02 14:30:00,000: INFO/MainProcess] [queue] => evaluation
```

---

## 启动顺序（严格遵守！）

```
1️⃣  启动 Redis       (其他服务依赖它)
     ↓ (等待 PONG)
2️⃣  启动 FastAPI     (监听 8000 端口)
     ↓ (并行启动可以)
3️⃣  启动 Celery Worker (监听队列)
     ↓ (并行启动可以)
4️⃣  启动前端 Vue     (npm run dev)
```

---

## 常见问题排查

### ❌ "Redis 连接失败"
**原因：** Redis 未运行  
**解决：**
```bash
# 检查是否运行
redis-cli ping

# 如果失败，启动 Redis
docker run -d -p 6379:6379 redis:latest
```

### ❌ "无法找到 Celery Worker"
**原因：** Worker 进程未启动  
**解决：**
```bash
# 检查 Worker 是否运行（看有无 ready 日志）
# 如果没有，执行启动命令

celery -A app.workers.celery_app worker -l info --pool=threads -Q evaluation,proofread,formatter,default
```

### ❌ "BAILIAN_API_KEY 未配置"
**原因：** AI API 密钥缺失  
**解决：**
```bash
# 编辑 backend/.env
BAILIAN_API_KEY=sk_xxxxx
# 或
DEEPSEEK_API_KEY=sk_xxxxx

# 重启 FastAPI
```

### ❌ "任务永远卡在 PENDING"
**原因：** Celery Worker 没有监听队列  
**检查清单：**
- [ ] Redis 是否运行？（redis-cli ping）
- [ ] Celery Worker 是否运行？（看启动终端）
- [ ] Worker 是否监听 evaluation 队列？（输出中有吗）
- [ ] API Key 是否配置？（.env）

---

## 测试评价功能

### 第一次测试

1. **打开浏览器控制台**
   ```
   F12 → Console
   ```

2. **访问评价页面**
   ```
   http://localhost:5173/evaluation
   ```

3. **上传 .docx 文件**
   - 选择论文类别
   - 选择一个测试 Word 文档

4. **观察日志输出**

   **后端（FastAPI 终端）：**
   ```
   [evaluation] 文件已保存: storage/uploads/xxxxxx.docx
   [evaluation] 结构提取完成: title='...' refs=20条
   [evaluation] 任务已入队 task_id=xxxxx status=pending
   ```

   **Celery Worker 终端：**
   ```
   [2026-04-02 14:30:05,000: INFO/MainProcess] Received task: app.workers.evaluation_tasks.run_evaluation[xxxxx]
   [2026-04-02 14:30:10,000: INFO/PoolWorker-1] [evaluation] 开始处理任务 task_id=xxxxx
   [2026-04-02 14:31:00,000: INFO/PoolWorker-1] [evaluation] 任务完成 task_id=xxxxx
   ```

   **前端浏览器控制台：**
   ```
   [evaluation store] 轮询开始...
   [evaluation store] 状态 (35%)
   [evaluation store] 状态 (70%)
   [evaluation store] 状态 completed (100%)
   ```

5. **看到评价报告即成功！**

---

## 一键启动脚本

### Windows (批处理)
创建文件 `start_services.bat`：

```batch
@echo off
chcp 65001 >nul
echo 启动论文评价系统...
echo.

REM 启动 Redis
echo [1/4] 启动 Redis...
docker run -d -p 6379:6379 redis:latest >nul 2>&1
timeout /t 2 >nul

REM 启动 FastAPI
echo [2/4] 启动 FastAPI...
start "FastAPI" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload"
timeout /t 3 >nul

REM 启动 Celery Worker
echo [3/4] 启动 Celery Worker...
start "Celery Worker" cmd /k "cd backend && venv\Scripts\activate && celery -A app.workers.celery_app worker -l info --pool=threads -Q evaluation,proofread,formatter,default"
timeout /t 2 >nul

REM 启动前端
echo [4/4] 启动前端...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ✅ 所有服务已启动！
echo.
echo 前端地址: http://localhost:5173
echo API文档: http://localhost:8000/docs
echo 诊断脚本: python backend/check_services.py
echo.
pause
```

运行：`start_services.bat`

---

## 完整文件结构检查

应该存在以下关键文件：
```
backend/
├── app/
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置文件（REDIS_HOST、API_KEY等）
│   ├── api/v1/
│   │   └── evaluation.py           # 评价 API（/upload、/status、/result）
│   └── workers/
│       ├── celery_app.py           # Celery 应用配置
│       └── evaluation_tasks.py     # 评价任务（实际执行评价）
├── .env                           # 环境变量（BAILIAN_API_KEY 等）
├── requirements.txt               # Python 依赖
└── check_services.py              # 诊断脚本（我们刚创建的）

frontend/
└── src/
    ├── views/Evaluation.vue       # 前端页面
    ├── store/modules/evaluation.js # Pinia 状态管理（轮询逻辑）
    └── api/evaluation.js          # API 调用（upload/status/result）
```

---

## 核心原理

### 为什么采用异步架构？
- **评价耗时长**（1-3分钟）：直接等待会导致 HTTP 超时
- **支持并发**：多个用户同时上传，服务器可并行处理
- **用户体验**：前端立即返回 task_id，显示进度条，不卡顿

### 为什么需要 Redis？
- **Celery Broker**：存储任务队列（待执行的任务）
- **Result Backend**：存储任务结果（已完成的任务）
- **没有 Redis**：任务无处可去，Celery Worker 拿不到任务

### 前端轮询机制
```javascript
// 每2秒查询一次
GET /api/v1/evaluation/status/{taskId}
{
  "status": "processing",  // pending | processing | completed | failed
  "progress": 35           // 0-100 的百分比
}
```

---

## 验证清单

完成启动后，逐一验证：

- [ ] `redis-cli ping` 返回 PONG
- [ ] http://localhost:8000/docs 能访问
- [ ] Celery Worker 终端显示 "ready" 和队列信息
- [ ] http://localhost:5173/evaluation 能打开
- [ ] 上传文件后后端有日志输出
- [ ] Celery Worker 有 "Received task" 日志
- [ ] 浏览器控制台有轮询日志
- [ ] 1-3 分钟后显示评价报告

---

## 获取帮助

如仍有问题，运行诊断脚本并保存输出：

```bash
cd backend
python check_services.py > diagnostic_report.txt 2>&1
```

然后查看 `diagnostic_report.txt` 中的详细错误信息。

---

**更新时间：2026-04-02**
