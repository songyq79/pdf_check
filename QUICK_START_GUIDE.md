# 论文评价系统 - 快速启动指南

## 问题描述
上传论文后卡在"正在检测中..."，进度条不动（5%）。

## 根本原因
系统架构采用 **Celery + Redis** 异步任务处理：
- 前端上传文件 → 后端立即返回 `task_id`
- 后端将评价任务提交到 Celery
- 前端每2秒轮询任务状态
- **如果 Redis 或 Celery Worker 未运行，任务永远卡在 PENDING 状态**

## 完整启动流程

### 1️⃣ 启动 Redis（任务队列 & 结果存储）

#### Windows - 使用 WSL2（推荐）
```bash
# 方法1：如果已装 Docker Desktop
docker run -d -p 6379:6379 redis:latest

# 方法2：如果已装 WSL2 + Redis
wsl
redis-server
```

#### Windows - 使用 Redis for Windows
```bash
# 下载：https://github.com/microsoftarchive/redis/releases
# 双击 redis-server.exe 启动
```

**验证 Redis 运行：**
```bash
redis-cli ping
# 应返回：PONG
```

---

### 2️⃣ 启动后端（FastAPI）

```bash
cd backend

# 第一次运行：创建虚拟环境
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置 API Key（重要！）
# 编辑 backend/.env 并设置：
#   BAILIAN_API_KEY=sk_xxxxx      （或 DEEPSEEK_API_KEY）

# 启动 FastAPI 服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验证后端运行：**
```
访问 http://localhost:8000/docs
应显示 Swagger API 文档
```

---

### 3️⃣ 启动 Celery Worker（执行评价任务）

**在后端目录新开一个终端：**

```bash
cd backend

# 激活虚拟环境（如果还没激活）
venv\Scripts\activate

# 启动 Celery Worker
celery -A app.workers.celery_app worker -l info --pool=threads -Q evaluation,proofread,formatter,default
```

**关键参数：**
- `-A app.workers.celery_app` - 指向 Celery 应用
- `-l info` - 日志级别
- `--pool=threads` - Windows 多线程模式（重要！）
- `-Q evaluation,proofread,formatter,default` - 监听的队列

**应该看到这样的输出：**
```
celery@DESKTOP-XXXXX ready.
- concurrency: 4 threads
- pool: threads
- clock: monotonic
[queue] => evaluation, proofread, formatter, default
[tasks] - app.workers.evaluation_tasks.run_evaluation
          app.workers.proofread_tasks.run_proofread
          ...
```

---

### 4️⃣ 启动前端（Vue）

**在前端目录新开一个终端：**

```bash
cd frontend

# 第一次运行：安装依赖
npm install

# 启动开发服务器
npm run dev
```

**应显示：**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

---

## 启动顺序（关键）

```
1️⃣  Redis      （最先，其他服务依赖它）
     ↓
2️⃣  FastAPI    （监听 8000 端口）
     ↓
3️⃣  Celery Worker （开始处理任务队列）
     ↓
4️⃣  前端 Vue   （可与步骤 2/3 并行启动）
```

---

## 测试评价功能

1. 打开 http://localhost:5173/evaluation
2. 选择论文类别
3. 上传 .docx 文件
4. **观察浏览器控制台（F12 → Console）和后端日志**

### 应该看到的日志

**后端（FastAPI）：**
```
[evaluation] 文件已保存: storage/uploads/xxxxx.docx
[evaluation] 结构提取完成: title='...' refs=20条
[evaluation] 任务已入队 task_id=xxxxx-xxxx-xxxx title='...' type=humanities
```

**Celery Worker：**
```
[2026-04-02 14:30:00,000: INFO/MainProcess] Received task: app.workers.evaluation_tasks.run_evaluation[xxxxx]
[2026-04-02 14:30:02,000: INFO/PoolWorker-1] [evaluation] 开始处理任务 task_id=xxxxx
[2026-04-02 14:30:45,000: INFO/PoolWorker-1] [evaluation] 任务完成 task_id=xxxxx
```

**前端（浏览器控制台）：**
```
[Evaluation] 文件选中: xxx.docx (size: 1234567)
[evaluation store] uploadAndEvaluate 开始上传
[evaluation store] 接收 task_id: xxxxx-xxxx-xxxx
[evaluation store] 轮询开始...
[evaluation store] 状态: processing (35%)
[evaluation store] 状态: completed (100%)
```

---

## 常见问题排查

### ❌ 错误："无法连接 Redis"
**解决：**
```bash
# 检查 Redis 是否运行
redis-cli ping

# 检查 .env 中的 REDIS_HOST 和 REDIS_PORT
REDIS_HOST=localhost
REDIS_PORT=6379
```

### ❌ 错误："未找到 Celery Worker"
**解决：**
```bash
# 确保 Celery Worker 进程运行
# 检查终端输出是否有 "ready." 标志

# 如果没有，重新启动：
celery -A app.workers.celery_app worker -l info --pool=threads
```

### ❌ 错误："BAILIAN_API_KEY 未配置"
**解决：**
```bash
# 编辑 backend/.env
BAILIAN_API_KEY=sk_xxxxx

# 或使用 DeepSeek（免费替代）：
DEEPSEEK_API_KEY=sk_xxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### ❌ 前端卡在进度 5%（无日志输出）
**检查清单：**
1. ✅ Redis 是否运行？（`redis-cli ping` 返回 PONG）
2. ✅ FastAPI 是否运行？（能访问 http://localhost:8000/docs）
3. ✅ Celery Worker 是否运行？（有 ready 日志）
4. ✅ 是否有 API Key？（BAILIAN_API_KEY 或 DEEPSEEK_API_KEY）

---

## 一键启动脚本（Windows）

创建 `start_all.bat`：

```batch
@echo off
echo 启动论文评价系统...

REM 打开 Redis（需提前配置路径）
start "Redis" redis-server

REM 等待 Redis 启动
timeout /t 2

REM 打开 FastAPI
start "FastAPI" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload"

REM 等待 FastAPI 启动
timeout /t 3

REM 打开 Celery Worker
start "Celery Worker" cmd /k "cd backend && venv\Scripts\activate && celery -A app.workers.celery_app worker -l info --pool=threads -Q evaluation,proofread,formatter,default"

REM 等待 Worker 启动
timeout /t 2

REM 打开前端
start "Vue Frontend" cmd /k "cd frontend && npm run dev"

echo 所有服务已启动！
echo 前端: http://localhost:5173
echo API: http://localhost:8000/docs
```

运行：`start_all.bat`

---

## 生产部署（Docker）

```bash
# 构建并启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 查看日志
docker-compose -f docker/docker-compose.yml logs -f
```

---

## 核心代码流程

### 前端上传流程
```
FileUpload 选择文件
  ↓
handleFileSelected() 触发上传
  ↓
evaluationStore.uploadAndEvaluate(file)
  ↓
evaluationAPI.upload(formData) → 返回 task_id
  ↓
startPolling(task_id) → 每2秒查询一次
  ↓
getStatus(task_id) → 返回 {status, progress}
  ↓
status === 'completed' → 显示结果
```

### 后端评价流程
```
POST /api/v1/evaluation/upload (file)
  ↓
validate_file + save_upload_file
  ↓
_extract_structure (解析文档)
  ↓
run_evaluation.apply_async (提交 Celery 任务)
  ↓
返回 {task_id, status: "pending"}
  ↓
[后台] Celery Worker 处理任务
  ↓
GET /api/v1/evaluation/status/{task_id}
  ↓
celery_app.AsyncResult 返回当前状态
```

---

## 支持 & 调试

如遇问题，查看日志：

```bash
# 后端日志（运行 FastAPI 的终端）
# 搜索 [evaluation]

# Celery 日志（运行 Worker 的终端）  
# 搜索 Received task / 任务完成

# 前端日志（浏览器 F12）
# 控制台输出 [Evaluation] / [evaluation store]
```

---

**祝您使用愉快！** 🎉
