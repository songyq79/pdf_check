# 宝塔面板 Celery Worker 配置指南

## 问题诊断
Celery Workers 连接到错误的 Redis 端口（6379 而非 26301）的原因是 `APP_ENV=production` 环境变量未被正确设置。

## 解决方案

### 1. 修改 Baota 面板中的 Celery Worker 启动命令

在 Baota 面板中，每个 Celery Worker 服务的启动命令都需要**前缀设置 `APP_ENV=production`**。

**修改前（错误）：**
```bash
celery -A app.workers.celery_app worker -Q evaluation --concurrency=4 --loglevel=info
```

**修改后（正确）：**
```bash
APP_ENV=production celery -A app.workers.celery_app worker -Q evaluation --concurrency=4 --loglevel=info
```

### 2. 需要修改的所有 Worker 服务

在 Baota 面板中，找到以下 Celery 服务并修改启动命令：

| 服务名称 | 修改后的启动命令 |
|---------|-----------------|
| celery (校对) | `APP_ENV=production celery -A app.workers.celery_app worker -Q proofread --concurrency=8 --loglevel=info` |
| celery2 (评价) | `APP_ENV=production celery -A app.workers.celery_app worker -Q evaluation --concurrency=4 --loglevel=info` |
| celery3 (格式化+查重) | `APP_ENV=production celery -A app.workers.celery_app worker -Q formatter,plagiarism -Q default --concurrency=6 --loglevel=info` |

### 3. 在 Baota 面板中应用修改的步骤

1. 打开 Baota 面板 → 左侧菜单 → 软件管理 或 应用中心
2. 找到 Celery 相关的服务列表
3. 对于每个 Celery Worker 服务：
   - 点击"编辑"或"修改启动命令"
   - 在启动命令最前面添加 `APP_ENV=production `
   - 点击保存
4. 重启所有 Celery Worker 服务：
   - 点击"重启"或停止后启动

### 4. 验证修改是否生效

修改并重启后，检查 Celery Worker 日志：

```bash
# 查看 worker 日志（根据实际路径调整）
tail -f /www/wwwlogs/celery_worker.log
```

**正确的日志输出示例：**
```
Connected to redis://:jzmNDJAF7b@localhost:26301/15
```

**错误的日志输出示例（需要修改）：**
```
Cannot connect to redis://localhost:6379/0
```

## 技术细节

### 为什么需要设置 APP_ENV？

1. `app/config.py` 中的 Settings 类使用 pydantic-settings 管理配置
2. 当 Celery Worker 启动时，它导入 `app.workers.celery_app`
3. `celery_app.py` 现在会检查 `APP_ENV` 环境变量，并加载对应的 `.env` 文件：
   - `APP_ENV=development` → 加载 `.env`（本地开发配置）
   - `APP_ENV=production` → 加载 `.env.production`（线上配置）

### celery_app.py 的修改

```python
# 必须在所有业务 import 之前加载 .env
app_env = os.getenv("APP_ENV", "development")
if app_env == "production":
    _env_path = Path(__file__).parent.parent.parent / ".env.production"
else:
    _env_path = Path(__file__).parent.parent.parent / ".env"

if _env_path.exists():
    load_dotenv(_env_path, override=True)
```

这确保在 Celery Worker 导入任何应用配置之前，正确的 Redis 连接字符串已经被加载。

## 故障排查

### 如果修改后仍然连接到 6379 端口

1. **确认 APP_ENV 被正确设置：**
   ```bash
   ps aux | grep celery
   # 检查输出中是否有 APP_ENV=production
   ```

2. **重启 Baota 面板中的 Celery Worker 服务（必须是重启，不是简单的刷新）**

3. **检查 `.env.production` 文件是否存在并包含正确的 Redis 配置：**
   ```bash
   cat /path/to/backend/.env.production | grep REDIS
   # 应该看到：
   # CELERY_BROKER_URL=redis://:jzmNDJAF7b@localhost:26301/15
   # REDIS_PORT=26301
   ```

4. **在宿主机直接测试 Redis 连接：**
   ```bash
   redis-cli -p 26301 -a jzmNDJAF7b -n 15 ping
   # 应该返回 PONG
   ```

5. **查看 Worker 启动日志的完整错误信息，反馈给开发者**

## 相关文件

- `.env` - 本地开发环境配置（localhost:6379/0）
- `.env.production` - 线上环境配置（localhost:26301/15，需要密码）
- `app/workers/celery_app.py` - Celery 应用工厂（已修复）
- `app/config.py` - 配置管理，使用 pydantic-settings
