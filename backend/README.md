# 论文助手系统 - 后端

FastAPI + Celery + Redis 构建的论文处理系统，提供错别字检查、智能评价、格式化、AI 校对四大功能。

## 目录结构

```
backend/
├── app/
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 统一配置（pydantic-settings）
│   │
│   ├── api/v1/                    # API 路由层
│   │   ├── router.py              # 路由总线
│   │   ├── spell_check.py         # 错别字检查接口
│   │   ├── evaluation.py          # 智能评价接口
│   │   ├── formatter.py           # 论文格式化接口
│   │   └── proofreadme.py         # AI 校对（高并发版）
│   │
│   ├── core/                      # 核心业务逻辑层
│   │   ├── ai_client.py           # 统一 AI 客户端（百炼→DeepSeek 自动 fallback）
│   │   ├── evaluator/
│   │   │   ├── prompts.py         # 评价维度 Prompt 模板
│   │   │   ├── chart_generator.py # 雷达图/柱状图生成
│   │   │   └── report_generator.py# Word 评价报告生成
│   │   ├── formatter/
│   │   │   ├── format_engine.py   # 格式化引擎（主入口）
│   │   │   ├── template_manager.py# 模板管理
│   │   │   ├── structure_analyzer.py # 文档结构识别
│   │   │   └── style_applicator.py   # 样式应用
│   │   └── proofreadme/
│   │       ├── pipeline.py        # 校对流水线（主入口）
│   │       ├── chunk.py           # 文本分块 + 保护词
│   │       ├── diff_engine.py     # 字符级 diff
│   │       ├── word_patch.py      # Word 修订节点生成
│   │       └── llm.py             # LLM 校对接口封装
│   │
│   ├── workers/                   # Celery 任务层
│   │   ├── celery_app.py          # Celery 工厂（broker/backend/队列配置）
│   │   ├── proofread_tasks.py     # 校对任务
│   │   ├── evaluation_tasks.py    # 评价任务
│   │   └── formatter_tasks.py     # 格式化任务
│   │
│   ├── schemas/                   # Pydantic 数据模型
│   │   ├── evaluation.py
│   │   ├── formatting.py
│   │   └── spell_check.py
│   │
│   ├── services/                  # 通用服务
│   │   └── file_service.py        # 文件上传/验证/清理
│   │
│   └── utils/                     # 工具函数
│       ├── exceptions.py          # 自定义异常
│       ├── file_utils.py          # 文件清理工具
│       └── logger.py              # 日志（loguru）
│
├── storage/                       # 运行时文件存储（gitignore）
│   ├── uploads/                   # 上传文件
│   ├── outputs/                   # 评价报告输出
│   ├── spell_check/               # 错别字检查临时文件
│   ├── proofreadme/               # AI 校对临时文件
│   ├── formatter/                 # 格式化临时文件
│   └── temp/                      # 其他临时文件
│
├── templates/                     # 格式化模板
│   ├── builtin/                   # 内置模板（学校/期刊）
│   └── user/                      # 用户上传模板
│
├── logs/                          # 日志文件（按日轮转）
├── requirements.txt
└── .env.example
```

## API 接口

| 模块 | 接口 | 说明 |
|------|------|------|
| 错别字检查 | `POST /api/v1/spell-check/upload` | 上传文档，后台校对 |
| | `GET /api/v1/spell-check/status/{id}` | 查询进度 |
| | `GET /api/v1/spell-check/download/{id}` | 下载结果 |
| 智能评价 | `POST /api/v1/evaluation/upload` | 上传论文，提交评价任务 |
| | `GET /api/v1/evaluation/status/{id}` | 查询进度 |
| | `GET /api/v1/evaluation/result/{id}` | 获取完整结果 |
| | `GET /api/v1/evaluation/download/{id}` | 下载 Word 报告 |
| 格式化 | `POST /api/v1/formatter/format` | 上传文档 + 模板ID，格式化 |
| | `GET /api/v1/formatter/templates` | 获取模板列表 |
| | `GET /api/v1/formatter/status/{id}` | 查询进度 |
| | `GET /api/v1/formatter/download/{id}` | 下载结果 |
| AI 校对 | `POST /api/v1/proofreadme/upload` | 高并发版校对 |
| | `GET /api/v1/proofreadme/status/{id}` | 查询进度 |
| | `GET /api/v1/proofreadme/download/{id}` | 下载结果 |

## 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env，填写 BAILIAN_API_KEY 或 DEEPSEEK_API_KEY
```

### 3. 启动 Redis（需要提前安装）
```bash
redis-server
```

### 4. 启动 Celery Worker
```bash
# Linux / macOS
celery -A app.workers.celery_app worker -l info -Q proofread,evaluation,formatter,default

# Windows（需要 --pool=solo）
celery -A app.workers.celery_app worker -l info --pool=solo -Q proofread,evaluation,formatter,default
```

### 5. 启动 FastAPI
```bash
python -m app.main
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 访问 API 文档
```
http://localhost:8000/docs
```

## 架构说明

**任务流转**：前端 → FastAPI（保存文件 + 提交任务 → 立即返回 task_id）→ Redis（消息队列）→ Celery Worker（执行 AI 处理）→ Redis（存储结果）→ 前端轮询 /status/{id} → 完成后 /download/{id}

**AI 双保险**：所有 AI 调用走统一的 `app.core.ai_client.call_ai()`，先尝试百炼（通义千问），失败自动切换 DeepSeek，每个模型最多重试 2 次。

**Track Changes**：校对结果使用 Word 原生修订标记（`w:del` / `w:ins`），用户在 Word 中可一键接受/拒绝每处修改。
