# 404 错误排查指南

## 问题现象
前端显示：
- ❌ "Not Found"
- ❌ "Request failed with status code 404"
- ❌ "评价失败"

## 排查步骤

### 1. 检查后端是否启动 ⭐⭐⭐（最重要）

#### 方法1：查看进程
```bash
# Windows (PowerShell)
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# 或者查看端口占用
netstat -ano | findstr :8000
```

#### 方法2：访问后端健康检查
在浏览器打开：`http://localhost:8000/health`

**期望结果**：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "bailian_configured": true,
  "deepseek_configured": false
}
```

**如果无法访问**，说明后端没有启动！

### 2. 启动后端服务

#### 在 PyCharm 中启动

**方式A：使用 main.py**
```bash
cd backend
python app/main.py
```

**方式B：使用 uvicorn 命令**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**启动成功的标志**：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
=======================================================
  论文评价检验系统  v1.0.0  启动
  API 文档: http://localhost:8000/docs
  存储路径: ...
=======================================================
```

### 3. 检查 Celery Worker 是否启动

智能评价功能需要 Celery Worker 处理异步任务。

#### 启动 Celery Worker
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

**注意**：Windows 上需要使用 `--pool=solo` 参数。

### 4. 检查 Redis 是否启动

Celery 需要 Redis 作为消息队列。

#### 检查 Redis
```bash
# 检查 Redis 是否运行
redis-cli ping
```

**期望结果**：`PONG`

#### 启动 Redis（如果未启动）
```bash
# Windows: 使用 Redis 安装目录下的命令
redis-server

# 或者使用 Docker
docker run -d -p 6379:6379 redis:latest
```

### 5. 检查前端配置

#### 查看 frontend/.env
```env
VITE_API_BASE_URL=http://localhost:8000
```

确保地址正确。

#### 重启前端开发服务器
```bash
cd frontend
npm run dev
```

### 6. 检查网络和防火墙

#### 测试后端连接
```bash
# 使用 curl 测试
curl http://localhost:8000/health

# 或使用 PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health
```

### 7. 查看后端日志

#### 日志位置
- 控制台输出
- `backend/logs/app_YYYY-MM-DD.log`

#### 查找错误信息
```bash
# 查看最新日志
tail -f backend/logs/app_*.log

# Windows PowerShell
Get-Content backend/logs/app_*.log -Tail 50 -Wait
```

## 完整启动流程（推荐）

### 第1步：启动 Redis
```bash
# Docker 方式（推荐）
docker run -d -p 6379:6379 --name redis redis:latest

# 或直接启动 Redis
redis-server
```

### 第2步：启动后端 API
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 第3步：启动 Celery Worker
```bash
# 新开一个终端
cd backend
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

### 第4步：启动前端
```bash
# 新开一个终端
cd frontend
npm run dev
```

### 第5步：验证
1. 访问 `http://localhost:8000/docs` - 查看 API 文档
2. 访问 `http://localhost:8000/health` - 检查健康状态
3. 访问 `http://localhost:5173` - 打开前端界面

## 常见问题

### Q1: 端口被占用
**错误信息**：`Address already in use`

**解决方法**：
```bash
# 查找占用 8000 端口的进程
netstat -ano | findstr :8000

# 杀死进程（替换 PID）
taskkill /PID <进程ID> /F
```

### Q2: Redis 连接失败
**错误信息**：`Error connecting to Redis`

**解决方法**：
1. 确保 Redis 已启动
2. 检查 `backend/.env` 中的 Redis 配置
3. 测试连接：`redis-cli ping`

### Q3: Celery Worker 无法启动
**错误信息**：`ValueError: not enough values to unpack`

**解决方法**：
Windows 上必须使用 `--pool=solo` 参数：
```bash
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

### Q4: 前端无法连接后端
**错误信息**：`Network Error` 或 `404`

**解决方法**：
1. 确认后端已启动（访问 `http://localhost:8000/health`）
2. 检查 `frontend/.env` 中的 `VITE_API_BASE_URL`
3. 清除浏览器缓存并刷新

### Q5: CORS 错误
**错误信息**：`Access-Control-Allow-Origin`

**解决方法**：
检查 `backend/app/config.py` 中的 CORS 配置：
```python
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
```

## 快速诊断命令

```bash
# 一键检查所有服务状态
echo "=== 检查 Redis ==="
redis-cli ping

echo "=== 检查后端 API ==="
curl http://localhost:8000/health

echo "=== 检查前端 ==="
curl http://localhost:5173

echo "=== 检查进程 ==="
netstat -ano | findstr "8000 6379 5173"
```

## 推荐的 PyCharm 配置

### 创建运行配置

#### 1. 后端 API
- **Script path**: `backend/app/main.py`
- **Working directory**: `backend`
- **Environment variables**: 
  ```
  PYTHONUNBUFFERED=1
  ```

#### 2. Celery Worker
- **Script**: `celery`
- **Parameters**: `-A app.workers.celery_app worker --loglevel=info --pool=solo`
- **Working directory**: `backend`

#### 3. 前端
- **Script**: `npm`
- **Parameters**: `run dev`
- **Working directory**: `frontend`

## 总结

**最可能的原因**：后端服务没有启动

**解决方案**：
1. 启动 Redis
2. 启动后端 API（`python app/main.py`）
3. 启动 Celery Worker
4. 刷新前端页面

**验证方法**：
访问 `http://localhost:8000/docs`，应该能看到 API 文档界面。
