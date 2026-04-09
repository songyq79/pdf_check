# 🚨 论文评价卡顿 - 快速修复清单

## 问题
✗ 上传论文后一直显示"正在检测中..."，进度条卡在 5%

---

## 快速修复（5分钟）

### 第一步：检查 Redis
```bash
redis-cli ping
```

**返回 `PONG`？** ✅ 跳到第二步  
**返回 `Could not connect`？** ❌ 运行：
```bash
docker run -d -p 6379:6379 redis:latest
```

---

### 第二步：检查 FastAPI
打开浏览器访问：
```
http://localhost:8000/docs
```

**能看到 Swagger 页面？** ✅ 跳到第三步  
**页面无法访问？** ❌ 运行：
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

---

### 第三步：检查 Celery Worker（最关键！）

**查看启动 Celery 的终端**，应该看到：
```
celery@DESKTOP-XXXXX ready.
- concurrency: 4 threads
- pool: threads
[queue] => evaluation, proofread, formatter, default
```

**看不到上面这些输出？** ❌ 运行：
```bash
cd backend
venv\Scripts\activate
celery -A app.workers.celery_app worker -l info --pool=threads -Q evaluation,proofread,formatter,default
```

---

### 第四步：检查 API Key

打开 `backend/.env` 文件，确保有以下之一：
```
BAILIAN_API_KEY=sk_xxxxx
```
或
```
DEEPSEEK_API_KEY=sk_xxxxx
```

**没有？** ❌ 加上去，然后重启 FastAPI

---

### 第五步：测试上传

1. 打开 http://localhost:5173/evaluation
2. 按 F12 打开浏览器控制台
3. 上传一个 .docx 文件
4. **观察 3 个终端的日志输出**：

#### FastAPI 终端应该显示：
```
[evaluation] 任务已入队 task_id=xxxxx
```

#### Celery Worker 终端应该显示：
```
[evaluation] 开始处理任务 task_id=xxxxx
[evaluation] 任务完成 task_id=xxxxx
```

#### 浏览器控制台应该显示：
```
[evaluation store] 轮询开始...
[evaluation store] 状态 (50%)
[evaluation store] 状态 completed (100%)
```

**看不到任何日志？** → 往上翻这个清单，检查哪一步没做好

---

## 启动顺序（严格！）

```
① Redis        ← 必须首先启动
   ↓ (等2秒)
② FastAPI      ← 需要 Redis
   ↓ (同时可以启动)
③ Celery Worker ← 需要 Redis
   ↓ (同时可以启动)
④ 前端 Vue
```

---

## 完整启动脚本（Windows）

### 方式1：手动逐个启动（推荐新手）

**终端1 - Redis：**
```bash
docker run -d -p 6379:6379 redis:latest
redis-cli ping
```

**终端2 - FastAPI：**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

**终端3 - Celery Worker：**
```bash
cd backend
venv\Scripts\activate
celery -A app.workers.celery_app worker -l info --pool=threads -Q evaluation,proofread,formatter,default
```

**终端4 - 前端：**
```bash
cd frontend
npm run dev
```

### 方式2：一键启动（需先配置）

创建 `start.bat`：
```batch
@echo off
docker run -d -p 6379:6379 redis:latest >nul 2>&1
start "FastAPI" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload"
start "Celery" cmd /k "cd backend && venv\Scripts\activate && celery -A app.workers.celery_app worker -l info --pool=threads -Q evaluation,proofread,formatter,default"
start "Frontend" cmd /k "cd frontend && npm run dev"
```

运行：`start.bat`

---

## 使用自动诊断脚本

```bash
cd backend
python check_services.py
```

这会告诉你：
- ✅ Redis 是否运行
- ✅ FastAPI 是否运行
- ✅ Celery Worker 是否运行
- ✅ API Key 是否配置

---

## 真正的错误排查（深度）

| 症状 | 原因 | 解决方案 |
|------|------|---------|
| 无法访问 http://localhost:8000 | FastAPI 未启动 | `uvicorn app.main:app --reload` |
| `redis-cli ping` 失败 | Redis 未启动 | `docker run -d -p 6379:6379 redis:latest` |
| Celery Worker 不启动 | 拼写错误或虚拟环境激活失败 | 检查命令、重新激活 venv |
| Celery 启动但任务不执行 | Worker 没有监听 evaluation 队列 | 检查启动命令中的 `-Q` 参数 |
| 任务执行失败 | BAILIAN_API_KEY / DEEPSEEK_API_KEY 未配置 | 编辑 .env，添加 API Key，重启 FastAPI |
| 只有一个进度条刷新（5%-50%） | 某个 AI 服务执行失败 | 查看 Celery Worker 的详细错误日志 |

---

## 最小可行验证（MVC）

```bash
# 检查 Redis
redis-cli ping
# 应返回：PONG

# 检查 FastAPI  
curl http://localhost:8000/docs
# 应返回 HTML 内容（不是 404）

# 检查 Celery Worker（查看其启动的终端输出）
# 应看到 "celery@DESKTOP-xxxxx ready"
```

---

## 常见"可以解决"的错误信息

### ❌ "Connection refused to Redis"
```bash
docker run -d -p 6379:6379 redis:latest
```

### ❌ "Cannot find module celery"
```bash
cd backend
pip install celery
```

### ❌ "ModuleNotFoundError: No module named 'app'"
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### ❌ "Port 8000 already in use"
```bash
# 找出占用 8000 的进程并杀死
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# 或改用其他端口
uvicorn app.main:app --port 8001
```

### ❌ "Invalid API-key provided"
```
编辑 backend/.env
BAILIAN_API_KEY=sk_xxxxx  # 改成真实的 key
重启 FastAPI
```

---

## 还是不行？

收集完整信息：

```bash
# 在 backend 目录运行
python check_services.py > report.txt 2>&1

# 然后在下面所有需要的文件中添加日志输出:
# 1. FastAPI 终端的所有输出 (复制粘贴)
# 2. Celery Worker 终端的所有输出 (复制粘贴)
# 3. report.txt 的内容

# 查看详细诊断报告
cat DIAGNOSIS_REPORT.md
```

---

## 成功标志

✅ 可以看到评价报告（有数字评分、维度分析等）  
✅ 浏览器能正常使用评价功能  
✅ 没有卡顿现象  

---

## 官方文档

- 详细启动指南：`QUICK_START_GUIDE.md`
- 完整诊断报告：`DIAGNOSIS_REPORT.md`
- 项目架构说明：`CLAUDE.md`

---

**更新时间：2026-04-02**
