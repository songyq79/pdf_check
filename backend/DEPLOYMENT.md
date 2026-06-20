# 多环境部署指南

## 环境配置结构

项目支持两套独立环境配置：

### 1. **本地开发环境** (`.env`)
- **用途**：本地开发测试
- **特点**：
  - `DEBUG=True` (开启调试模式)
  - Redis 默认配置 (localhost:6379，无密码)
  - SQLite 数据库
  - 较宽松的日志级别

### 2. **线上生产环境** (`.env.production`)
- **用途**：阿里云宝塔生产部署
- **特点**：
  - `DEBUG=False` (关闭调试模式)
  - Redis 特定配置 (localhost:26301，密码：jzmNDJAF7b，数据库15)
  - SQLite 数据库
  - 强 `SECRET_KEY`

## 使用方法

### 本地开发
```bash
# 1. 配置本地 Redis（可选，有默认值）
# Redis 需运行在 localhost:6379（默认）

# 2. 应用会自动加载 .env 文件
python -c "from app.config import settings; print(f'Loaded: {settings.CELERY_BROKER_URL}')"

# 输出: Loaded: redis://localhost:6379/0
```

### 线上生产部署（宝塔）
```bash
# 1. 在宝塔服务器上设置环境变量
export APP_ENV=production

# 2. 启动应用（Celery Worker + API）
# 此时会自动加载 .env.production 文件
APP_ENV=production python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或用 Celery Worker：
APP_ENV=production celery -A app.workers.celery_app worker --loglevel=info
```

## 配置优先级

当应用启动时，配置加载的优先级为：

```
系统环境变量 > .env/.env.production 文件 > config.py 默认值
```

### 示例
```bash
# 如果既设置环境变量又有 .env 文件，环境变量优先
export REDIS_PORT=26301
# 即使 .env 中有 REDIS_PORT=6379，也会使用 26301
```

## 部署检查清单

### 宝塔部署前

- [ ] `.env.production` 文件已创建并配置正确
- [ ] 确认 Redis 在 localhost:26301 运行，密码正确
- [ ] SECRET_KEY 已设置为强随机字符串（不是默认值）
- [ ] DEBUG 已关闭 (`DEBUG=False`)

### 部署命令

```bash
# 1. 设置环境变量
export APP_ENV=production

# 2. 验证配置加载（应该看到生产配置）
APP_ENV=production python -c "
from app.config import settings
print(f'Environment: {settings.DEBUG}')
print(f'Redis: {settings.CELERY_BROKER_URL}')
print(f'Env file used: .env.production')
"

# 预期输出：
# Environment: False
# Redis: redis://:jzmNDJAF7b@localhost:26301/15
# Env file used: .env.production

# 3. 测试 Redis 连接
redis-cli -h localhost -p 26301 -a jzmNDJAF7b -n 15 ping
# 应该返回：PONG

# 4. 启动应用服务
# FastAPI
APP_ENV=production gunicorn app.main:app -w 4 --bind 0.0.0.0:8000

# Celery Worker
APP_ENV=production celery -A app.workers.celery_app worker \
  --loglevel=info \
  --queues=proofread,evaluation,formatter,plagiarism,default \
  --concurrency=128 \
  --pool=threads
```

## 常见问题

### Q: 为什么配置没有加载？
A: 检查 `APP_ENV` 环境变量是否正确设置：
```bash
echo $APP_ENV  # 应该显示 production 或 development
```

### Q: 本地开发时想临时用生产配置测试？
A: 临时设置环境变量：
```bash
APP_ENV=production python your_script.py
```

### Q: 生产环境想查看当前加载的配置？
A: 在宝塔面板中运行：
```bash
APP_ENV=production python -c "from app.config import settings; print(settings.model_dump())"
```

## 文件清单

```
backend/
├── .env                   # 本地开发配置（Git 忽略）
├── .env.production        # 线上生产配置（Git 忽略）
├── .env.example          # 配置示例（提交到 Git）
├── app/
│   ├── config.py         # 配置加载逻辑（支持 APP_ENV）
│   ├── main.py
│   └── workers/
│       └── celery_app.py
└── DEPLOYMENT.md         # 本文件
```

## 额外说明

- `.env` 和 `.env.production` 文件**不应**提交到 Git（已在 .gitignore 中）
- 使用 `.env.example` 作为配置模板文档
- 每次拉取新代码后，确认 APP_ENV 环境变量正确
