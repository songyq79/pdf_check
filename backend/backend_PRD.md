# 论文智能检验系统 — 后端产品需求文档

> **版本：** v1.2  
> **框架：** FastAPI + Celery + Redis  
> **语言：** Python 3.12  
> **最后更新：** 2026-03  

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [完整目录结构](#3-完整目录结构)
4. [环境配置](#4-环境配置)
5. [API 接口规范](#5-api-接口规范)
6. [核心模块详解](#6-核心模块详解)
7. [任务队列设计](#7-任务队列设计)
8. [数据模型](#8-数据模型)
9. [文件存储规范](#9-文件存储规范)
10. [错误处理规范](#10-错误处理规范)
11. [性能优化记录](#11-性能优化记录)
12. [已知问题与待解决项](#12-已知问题与待解决项)
13. [部署说明](#13-部署说明)
14. [后续迭代规划](#14-后续迭代规划)

---

## 1. 项目概述

### 1.1 产品定位

面向高校师生的**论文辅助处理平台**，提供三大核心能力：

| 功能模块 | 描述 | 技术路线 |
|---|---|---|
| 智能评价 | 四维度 AI 评价论文质量，生成 Word 报告含雷达图 | 大模型 + matplotlib |
| 错别字检查 | AI 校对全文，以 Word 修订模式标注修改建议 | 大模型 + python-docx OOXML |
| 模板排版 | 按高校/期刊模板自动格式化论文 | 规则引擎 + 样式映射 |

### 1.2 核心设计原则

1. **内容零丢失**：所有修改以 Word Track Changes 写入，不直接改原文
2. **异步优先**：所有耗时操作通过 Celery 任务队列处理，接口即时返回 task_id
3. **双模型备用**：百炼/通义千问主力，DeepSeek 自动 fallback，保证 AI 服务可用性
4. **格式完整保留**：校对时保留段落 `w:pPr` 和 run 样式 `w:rPr`，不破坏原文格式

---

## 2. 系统架构

```
前端（Vue 3，端口 5173/5174）
        │ HTTP/CORS
        ▼
FastAPI 主服务（端口 8000）
   ├── /api/v1/evaluation   智能评价
   ├── /api/v1/proofread    错别字检查
   └── /api/v1/formatter    模板排版
        │ 任务分发（apply_async）
        ▼
Celery Worker
   ├── Queue: evaluation    AI 并发评价四维度
   ├── Queue: proofread     逐段落 AI 校对
   └── Queue: formatter     文档结构分析+样式应用
        │ Broker + Result Backend
        ▼
Redis（localhost:6379）
        │ API 调用
        ▼
百炼/通义千问（主）─── 失败自动切换 ───► DeepSeek（备）
```

### 2.1 请求生命周期

```
上传文件
  → FastAPI 保存文件，生成 task_id
  → 提交 Celery 异步任务
  → 立即返回 {task_id, status_url}
  → 前端轮询 status 接口
  → 任务完成后调用 download/result 接口获取结果
```

---

## 3. 完整目录结构

```
pdf_check/
├── backend/
│   ├── app/
│   │   ├── main.py                         # FastAPI 入口，CORS，全局异常，/health
│   │   ├── config.py                       # 统一配置（pydantic-settings，读取 .env）
│   │   │
│   │   ├── api/v1/
│   │   │   ├── router.py                   # 路由总线，注册三大模块前缀
│   │   │   ├── evaluation.py               # 智能评价：upload/status/result/download
│   │   │   ├── proofread.py                # 错别字：upload/status/download/撤销
│   │   │   └── formatter.py                # 排版：format/templates/status/download/preview
│   │   │
│   │   ├── core/
│   │   │   ├── ai_client.py                # 统一 AI 调用（百炼→DeepSeek 自动切换）
│   │   │   │
│   │   │   ├── evaluator/
│   │   │   │   ├── prompts.py              # 四维度评价提示词模板
│   │   │   │   ├── report_generator.py     # Word 评价报告生成（含雷达图插入）
│   │   │   │   └── chart_generator.py      # matplotlib 雷达图/柱状图生成
│   │   │   │
│   │   │   ├── proofreadme/
│   │   │   │   ├── pipeline.py             # 校对核心流水线（段落遍历/并发/写修订）
│   │   │   │   ├── llm.py                  # 校对 AI 调用封装（三层 prompt）
│   │   │   │   ├── chunk.py                # 文本分块 + 专有词保护/还原
│   │   │   │   ├── diff_engine.py          # 字符级 diff（SequenceMatcher）
│   │   │   │   └── word_patch.py           # OOXML w:del/w:ins 修订节点生成
│   │   │   │
│   │   │   └── formatter/
│   │   │       ├── format_engine.py        # 格式化引擎主入口（五步流程）
│   │   │       ├── template_manager.py     # 模板 CRUD、索引、配置提取、缓存
│   │   │       ├── structure_analyzer.py   # 文档结构识别（5层策略）
│   │   │       └── style_applicator.py     # 样式应用（页面/字体/段落/编号/页眉页脚）
│   │   │
│   │   ├── workers/
│   │   │   ├── celery_app.py               # Celery 配置：队列、超时、pool=threads
│   │   │   ├── evaluation_tasks.py         # 评价 Task：四维度并发 + 报告生成
│   │   │   ├── proofread_tasks.py          # 校对 Task：调用 process_word_sync
│   │   │   └── formatter_tasks.py          # 格式化 Task：调用 FormatEngine
│   │   │
│   │   ├── models/
│   │   │   ├── task.py                     # 任务状态模型（预留 DB 扩展）
│   │   │   └── user.py                     # 用户模型（预留）
│   │   │
│   │   ├── schemas/
│   │   │   ├── evaluation.py               # EvaluationResult / EvaluationResponse
│   │   │   ├── formatting.py               # FormatRequest / FormatStatusResponse
│   │   │   └── spell_check.py              # SpellCheckStatusResponse
│   │   │
│   │   ├── services/
│   │   │   ├── cache_service.py            # Redis 缓存封装（预留）
│   │   │   ├── file_service.py             # 文件上传、保存、校验、清理
│   │   │   └── task_service.py             # 任务状态查询封装（预留）
│   │   │
│   │   └── utils/
│   │       ├── exceptions.py               # AppException / FileValidationError / AIServiceError
│   │       ├── file_utils.py               # 文件工具函数
│   │       └── logger.py                   # loguru 日志配置
│   │
│   ├── workers/                            # Celery worker 启动入口（独立进程）
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── storage/                            # 运行时文件存储（gitignore）
│   │   ├── formatter/                      # 排版输入/输出
│   │   ├── outputs/                        # 评价报告输出
│   │   ├── proofread/                      # 校对输入/输出
│   │   ├── temp/                           # 临时文件
│   │   └── uploads/                        # 上传文件
│   │
│   ├── templates/                          # 格式化模板库
│   │   ├── builtin/                        # 内置模板（.docx + .json 元数据）
│   │   └── user/custom/                    # 用户上传自定义模板
│   │
│   ├── logs/                               # 运行日志
│   ├── .env                                # 环境变量（不提交 git）
│   ├── .env.example                        # 环境变量示例
│   ├── config.py                           # 根级配置
│   ├── Dockerfile
│   ├── generate_templates.py               # 批量生成内置模板脚本
│   ├── requirements.txt                    # 完整依赖
│   └── requirements-core.txt              # 最小核心依赖
│
├── database/                               # 数据库相关（预留）
├── .venv/                                  # Python 虚拟环境
└── .claude/                                # Claude 配置
```

---

## 4. 环境配置

`.env` 文件位于 `backend/` 目录根部：

```env
# ── AI 服务（至少配置其中一个）────────────────────────────────
BAILIAN_API_KEY=your_bailian_key          # 百炼/通义千问（主力）
BAILIAN_MODEL=qwen-max
BAILIAN_TIMEOUT=60                         # 评价模块超时（秒），校对模块固定20s

DEEPSEEK_API_KEY=your_deepseek_key         # DeepSeek（自动备用）
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

# ── Redis ──────────────────────────────────────────────────────
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ── 功能开关 ───────────────────────────────────────────────────
USE_AI=False                               # 格式化是否启用 AI 辅助结构识别
DEBUG=False

# ── 文件限制 ───────────────────────────────────────────────────
MAX_FILE_SIZE=20                           # 最大文件大小（MB）

# ── CORS（前端地址白名单）──────────────────────────────────────
# ⚠️ Vite 默认5173，被占用时自动切换5174，两个都要配！
CORS_ORIGINS=["http://localhost:5173","http://localhost:5174","http://127.0.0.1:5173","http://127.0.0.1:5174"]
```

### 4.1 AI 客户端超时参数说明

| 参数 | 校对模块 | 评价模块 | 说明 |
|---|---|---|---|
| `timeout` | 20s（固定） | `BAILIAN_TIMEOUT`（60s） | 校对段落失败跳过；评价需完整响应 |
| `retries` | 1次/模型 | 1次/模型 | 最坏情况：百炼20s + DeepSeek20s = 40s |
| 模型切换 | 自动 | 自动 | 百炼全失败后自动切 DeepSeek |

> ⚠️ `evaluation_tasks.py` 显式传 `timeout=settings.BAILIAN_TIMEOUT`，不受 `ai_client.py` 默认值变更影响。

---

## 5. API 接口规范

**Base URL：** `http://localhost:8000/api/v1`

**通用任务状态枚举：**

| status | 说明 |
|---|---|
| `pending` | 排队等待 |
| `processing` | 执行中 |
| `completed` | 成功完成 |
| `failed` | 执行失败 |
| `cancelled` | 已撤销 |

---

### 5.1 智能评价模块

#### `POST /evaluation/upload`

上传论文，提交 AI 四维度评价任务。

**请求：** `multipart/form-data`，参数 `file`（.docx，≤20MB）

**处理逻辑：**
1. 校验格式/大小
2. 检查 AI API Key（未配则返回 503）
3. 解析文档：第一个非空段落为标题，正文最多截取 30000 字
4. 提交 Celery 任务到 `evaluation` 队列

**响应：**
```json
{
  "task_id": "uuid",
  "status": "pending",
  "paper_title": "自动提取的论文标题",
  "status_url": "/api/v1/evaluation/status/{task_id}",
  "result_url": "/api/v1/evaluation/result/{task_id}",
  "message": "任务已提交，多维度评价正在后台并发执行"
}
```

---

#### `GET /evaluation/status/{task_id}`

轮询任务进度。

| Celery 状态 | 返回 status | progress |
|---|---|---|
| PENDING | pending | 0 |
| STARTED | processing | 40 |
| RETRY | processing | 20 |
| SUCCESS | completed | 100 |
| FAILURE | failed | 0 |

---

#### `GET /evaluation/result/{task_id}`

获取完整评价结果（任务完成后调用）。

**响应：**
```json
{
  "paper_title": "论文标题",
  "overall_score": 85.5,
  "evaluated_at": "2026-01-01T12:00:00",
  "report_id": "uuid",
  "report_download_url": "/api/v1/evaluation/download/{report_id}",
  "dimensions": {
    "academic_standard": {
      "dimension_name": "学术规范性",
      "score": 88,
      "strengths": ["结构完整", "格式规范"],
      "weaknesses": ["部分术语不够准确"],
      "suggestions": ["建议统一学术术语"]
    },
    "logic_innovation": { "..." },
    "language_quality": { "..." },
    "citation_standard": { "..." }
  }
}
```

---

#### `GET /evaluation/download/{report_id}`

下载 Word 格式评价报告（含雷达图）。

**报告结构：**
- 论文标题 + 评价时间
- 综合评分（大字号，颜色按分段）+ 评价等级（A/B/C/D/F）
- 四维度雷达图（matplotlib polar，300dpi PNG 嵌入）
- 逐维度详细评价（优点/不足/建议，项目符号列表）
- 页脚：「本报告由论文智能评价系统自动生成」

**评分颜色规则：**

| 分数 | 等级 | 颜色 |
|---|---|---|
| ≥90 | 优秀 (A) | 绿色 |
| ≥80 | 良好 (B) | 蓝色 |
| ≥70 | 中等 (C) | 橙色 |
| ≥60 | 及格 (D) | 深橙色 |
| <60 | 不及格 (F) | 红色 |

**文件名：** `论文评价报告_YYYYMMDD_HHMMSS.docx`

---

### 5.2 错别字检查模块

#### `POST /proofread/upload`

上传文档，提交 AI 校对任务（固定 `full` 模式）。

**响应：**
```json
{
  "task_id": "uuid",
  "filename": "原文件名.docx",
  "status": "pending",
  "status_url": "/api/v1/proofread/status/{task_id}",
  "message": "文件已上传，正在后台进行AI校对"
}
```

---

#### `GET /proofread/status/{task_id}`

**Celery 状态 → 进度映射：**

| Celery 状态 | status | progress |
|---|---|---|
| PENDING | pending | 0 |
| STARTED | processing | 20 |
| PROGRESS | processing | 从 meta.progress 读取真实进度 |
| SUCCESS | completed | 100 |
| FAILURE | failed | 0 |

**completed 时额外字段：**
```json
{
  "download_url": "/api/v1/proofread/download/{task_id}",
  "finished_at": "2026-01-01T12:00:00",
  "stats": {
    "total": 120,
    "changed": 15,
    "skipped": 105
  }
}
```

> `total`=实际检查段落数，`changed`=有修改段落数，`skipped`=跳过段落数（图片/极短/纯英文/参考文献行）

---

#### `GET /proofread/download/{task_id}`

下载校对结果文档（含 Word 修订标记，用户可在 Word 中逐条接受/拒绝）。

**文件名：** `AI_校对_YYYYMMDDHHMMSS.docx`

---

#### `DELETE /proofread/task/{task_id}`

撤销任务（仅 pending/processing 状态有效）。

**响应：**
```json
{ "task_id": "uuid", "status": "cancelled", "message": "任务已撤销" }
```

---

### 5.3 模板排版模块

#### `GET /formatter/templates`

获取模板列表，支持分类过滤和关键词搜索，按 `usage_count` 降序。

**Query 参数：** `category`（universities/journals/custom）、`search`（关键词）

**响应：**
```json
{
  "success": true,
  "total": 4,
  "categories": {"universities": 2, "journals": 1, "custom": 1},
  "templates": [{
    "id": "template_id",
    "name": "模板名称",
    "category": "universities",
    "school_or_journal": "某大学",
    "description": "模板描述",
    "usage_count": 10
  }]
}
```

---

#### `POST /formatter/format`

上传文档并提交格式化任务。

**请求：** `multipart/form-data`，参数 `file`（.docx）+ `template_id`（字符串）

**响应：**
```json
{
  "success": true,
  "task_id": "uuid",
  "status": "pending",
  "status_url": "/api/v1/formatter/status/{task_id}",
  "download_url": "/api/v1/formatter/download/{task_id}"
}
```

---

#### `GET /formatter/status/{task_id}`

**completed 时额外字段：**
```json
{
  "result": { "sections": 12, "applied": 12, "errors": 0, "quality": 0.85 },
  "download_url": "/api/v1/formatter/download/{task_id}"
}
```

---

#### `GET /formatter/download/{task_id}`

下载排版后文档，文件名：`格式化_原文件名.docx`

---

#### `POST /formatter/templates/upload`

上传自定义模板，服务端验证后存入 `templates/user/custom/`。

**请求参数：** `file`（.docx）、`name`、`category`（默认 custom）、`school_or_journal`、`description`

**验证规则：** 页面尺寸不小于10cm×10cm；可无自定义样式（仅 warning）

---

#### `POST /formatter/preview`

预览文档结构，不格式化，仅分析返回结构信息。

**响应字段：** `sections`（识别章节列表）、`stats`（段落统计）、`quality`（识别质量0~1）、`outline`（Markdown 大纲）

---

## 6. 核心模块详解

### 6.1 AI 客户端（`core/ai_client.py`）

**调用链：**

```
call_ai(prompt, retries=1, timeout=20.0)
  ├── 尝试 百炼/千问（_call_qwen → asyncio.to_thread 包装同步SDK）
  │     └── 超时/失败 → 切换
  └── 尝试 DeepSeek（_call_deepseek → AsyncOpenAI）
        └── 全失败 → raise RuntimeError
```

**parse_json_response：** 自动剥离 ` ```json ` 代码块，解析失败返回 fallback，不抛异常。

---

### 6.2 智能评价引擎（`core/evaluator/`）

#### 四大评价维度

| 维度 Key | 中文名 | 评价角度 |
|---|---|---|
| `academic_standard` | 学术规范性 | 结构完整性、学术用语、格式规范 |
| `logic_innovation` | 逻辑与创新性 | 论证逻辑、研究创新性、论据充分性 |
| `language_quality` | 语言质量 | 术语准确性、表达清晰度、语言简洁性 |
| `citation_standard` | 文献引用规范性 | 参考文献格式（GB/T 7714等）、引用合理性、标注准确性 |

#### 评价流程

```
上传 .docx
  → 提取标题（第一个非空段落）
  → 提取正文（最多30000字，超长截断）
  → asyncio.gather 四维度并发 AI 调用（互不阻塞）
  → 每维度返回 {score(0-100), strengths[], weaknesses[], suggestions[]}
  → 综合评分 = 四维度均值（保留1位小数）
  → ReportGenerator 生成 Word 报告：
      ├── ChartGenerator 生成雷达图 PNG（matplotlib polar，300dpi）
      ├── 插入雷达图到报告
      └── 逐维度写入详细评价内容
```

---

### 6.3 校对流水线（`core/proofreadme/`）

#### 校对模式

| 模式 | 内容 | 接口使用 |
|---|---|---|
| `basic` | 仅错别字 + 标点 | 未启用 |
| `full` | 错别字 + 语法 + 段落逻辑（**一次 AI 调用完成三层检查**） | ✅ 默认 |

#### 处理流程

```
1. 文件有效性检测（空文件/损坏文件提前返回错误，避免永久 pending）
2. _collect_tasks：遍历文档
   ├── 正文段落（跳过表格内段落，避免重复）
   └── 表格单元格（独立收集）
3. asyncio.gather 并发处理（Semaphore=16）
   │
   每个段落：
   ├── _has_drawing → 跳过（图片段落绝不触碰）
   ├── _is_empty_para → 跳过
   ├── _should_skip_para → 跳过以下三类：
   │     ├── 极短段落（≤4字）
   │     ├── 无中文内容（纯英文/数字/符号）
   │     └── 参考文献行（[1]/1. 开头且<200字）
   │
   └── 需要校对的段落：
       ├── protect_terms（专有词→占位符）
       ├── full_proofread / proofread_text（AI 调用）
       ├── _check_placeholders（占位符完整性校验，失败则放弃该段落）
       ├── restore_terms（占位符→原词）
       ├── compute_diff（字符级 SequenceMatcher diff）
       └── _write_revision（写入 w:del/w:ins 修订节点）
4. doc.save(output_path)
```

#### 专有词保护机制（`chunk.py`）

以下内容替换为占位符 `__PROTxxxxxx_0000__`，校对后精确还原：

- LaTeX 公式（块公式 `$$...$$`、行内公式 `$...$`）
- 参考文献编号（`[1]`、`[1,2]`、`[1-3]`，含前置空格）
- URL、邮箱
- 英文单词/缩写
- 百分比、日期、带单位数字（mm/cm/kg/℃/Hz等）、纯数字
- 格式空格（全角 `\u3000`、连续半角空格）

**占位符二次保护：** 替换后对占位符紧邻的单个空格并入占位符，防止 AI 把 `__PROT__ 欧盟` 中的空格当多余空格删除。

**严格校验：** AI 返回后比对原始 token 列表与返回 token 列表，数量或顺序不一致则**放弃该段落修改**，确保内容零丢失。

#### 修订节点写入（`word_patch.py`）

生成符合 OOXML 规范的修订节点：

```xml
<!-- 替换：删除原文 + 插入新文 -->
<w:del w:id="1" w:author="AI-Proofreader" w:date="...">
  <w:r><w:delText>原文片段</w:delText></w:r>
</w:del>
<w:ins w:id="2" w:author="AI-Proofreader" w:date="...">
  <w:r><w:t>修正片段</w:t></w:r>
</w:ins>
```

---

### 6.4 格式化引擎（`core/formatter/`）

#### 五步格式化流程

```
[1/5] 加载文档        Document(input_path)
[2/5] 识别结构        StructureAnalyzer.analyze(doc)
[3/5] 加载模板        TemplateManager.extract_config(template_id)  ← 内存缓存
[4/5] 应用样式        StyleApplicator.apply(doc, sections)
[5/5] 保存文档        doc.save(output_path)
```

#### 结构识别策略（五层优先级）

| 优先级 | 策略 | 置信度 |
|---|---|---|
| 1 | 关键词匹配（摘要/Abstract/参考文献/致谢等） | 0.95 |
| 2 | 编号模式匹配（第X章/1.1/1.1.1等正则） | 0.90 |
| 3 | Word 内置样式（Heading1~4/标题1~3） | 0.85 |
| 4 | 格式特征（字号≥22加粗=标题，≥16=章标题） | 0.75 |
| 5 | AI 辅助识别（`USE_AI=True` 时启用） | 0.80 |

**识别章节类型：** `title / author / abstract_cn / abstract_en / keywords_cn / keywords_en / toc / chapter / section_1~3 / figure / table / formula / references / appendix / acknowledgement / body / unknown`

#### 识别质量评分算法

`quality = 置信度均值×0.4 + 完整性得分×0.3 + 方法多样性×0.3`

完整性：有标题+0.1、有摘要+0.1、有章节+0.05、有参考文献+0.05

#### 模板管理（`template_manager.py`）

- **两级目录**：内置模板（`builtin/`，不可删）+ 用户模板（`user/`，可删）
- **元数据格式**：每个模板 `.docx`（样式源）+ `.json`（TemplateMetadata）
- **启动扫描**：构建内存索引 `_template_index`，无需频繁读盘
- **配置缓存**：`_config_cache` 缓存解析后的 `TemplateConfig`，重复使用无需重解析
- **写盘异步化**：使用次数更新在后台 `daemon` 线程写 JSON，不阻塞主流程

---

## 7. 任务队列设计

### 7.1 Celery 配置（`workers/celery_app.py`）

| 配置项 | 值 | 说明 |
|---|---|---|
| `worker_pool` | `threads` | 多线程，Windows/Linux 均支持 |
| `worker_prefetch_multiplier` | 1 | 每次只预取1个，防长任务阻塞 |
| `task_soft_time_limit` | 540s | 软超时，优雅退出 |
| `task_time_limit` | 600s | 强超时，强制终止 |
| `task_acks_late` | True | 完成后 ACK，崩溃时自动重新入队 |
| `task_reject_on_worker_lost` | True | Worker 丢失时任务重入队 |
| `result_expires` | 86400s | 结果保留24小时 |
| `timezone` | Asia/Shanghai | — |

### 7.2 队列分配与重试策略

| 队列 | 任务 | max_retries | 说明 |
|---|---|---|---|
| `evaluation` | 评价任务 | 1次，delay=15s | 四维度并发，单任务耗时较长 |
| `proofread` | 校对任务 | 2次 | 逐段处理，失败可重试 |
| `formatter` | 格式化任务 | 1次 | CPU密集，速度较快 |
| `default` | 其他 | — | — |

### 7.3 启动命令

```bash
# 开发（全队列）
celery -A app.workers.celery_app worker --loglevel=info -Q proofread,evaluation,formatter,default

# 生产（分队列并发）
celery -A app.workers.celery_app worker -Q evaluation --concurrency=2
celery -A app.workers.celery_app worker -Q proofread  --concurrency=4
celery -A app.workers.celery_app worker -Q formatter  --concurrency=4

# 监控
celery -A app.workers.celery_app flower --port=5555
```

---

## 8. 数据模型

### 8.1 EvaluationResult

| 字段 | 类型 | 说明 |
|---|---|---|
| `dimension_name` | str | 维度中文名 |
| `score` | int (0-100) | 维度得分 |
| `strengths` | List[str] | 优点列表 |
| `weaknesses` | List[str] | 不足列表 |
| `suggestions` | List[str] | 改进建议列表 |

### 8.2 EvaluationResponse

| 字段 | 类型 | 说明 |
|---|---|---|
| `paper_title` | str | 论文标题（文档提取） |
| `overall_score` | float (0-100) | 综合评分（四维度均值） |
| `dimensions` | Dict[str, EvaluationResult] | 各维度结果 |
| `evaluated_at` | datetime | 评价完成时间 |
| `report_id` | str? | 报告文件 ID |
| `report_download_url` | str? | 报告下载地址 |

### 8.3 TemplateMetadata

| 字段 | 类型 | 说明 |
|---|---|---|
| `template_id` | str | 唯一 ID |
| `name` | str | 模板名称 |
| `category` | str | universities / journals / custom |
| `school_or_journal` | str | 学校或期刊名 |
| `version` | str | 默认 1.0 |
| `usage_count` | int | 使用次数（推荐排序） |
| `is_public` | bool | True=内置不可删 |
| `file_path` | str | 本地文件路径 |

### 8.4 自定义异常

| 异常类 | HTTP 状态码 | 场景 |
|---|---|---|
| `AppException` | 400 | 通用业务异常 |
| `FileValidationError` | 400 | 文件格式/大小校验失败 |
| `AIServiceError` | 503 | AI API Key 未配置 |
| `ReportGenerationError` | — | 报告生成失败（内部捕获） |
| `ChartGenerationError` | — | 雷达图生成失败（内部捕获，报告仍可生成） |

---

## 9. 文件存储规范

| 目录 | 用途 | 文件命名 |
|---|---|---|
| `storage/uploads/` | 评价上传文件 | `{uuid}.docx` |
| `storage/outputs/` | 评价报告+雷达图 | `{report_id}_report.docx`、`{report_id}_report_radar.png` |
| `storage/proofread/` | 校对输入/输出 | `{task_id}_in.docx` / `{task_id}_out.docx` |
| `storage/formatter/` | 排版输入/输出 | `{task_id}_input.docx` / `{task_id}_output.docx` |
| `templates/builtin/` | 内置模板 | `名称.docx` + `名称.json` |
| `templates/user/custom/` | 用户模板 | `{uuid[:16]}.docx` + `{uuid[:16]}.json` |

**保留策略：** Redis 结果24小时后自动过期；`storage/` 下实体文件需单独配置清理任务（待实现）。

---

## 10. 错误处理规范

### 10.1 HTTP 状态码

| 状态码 | 场景 |
|---|---|
| 200 | 成功 |
| 400 | 文件格式错误、参数错误、任务状态不允许此操作 |
| 404 | 文件不存在或已过期 |
| 413 | 文件超过大小限制（>20MB） |
| 503 | AI API Key 未配置 |
| 500 | 服务器内部错误（全局兜底） |

### 10.2 健康检查

```
GET /health
```
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "bailian_configured": true,
  "deepseek_configured": false
}
```

---

## 11. 性能优化记录

### v1.1 性能优化（已上线）

| 优化项 | 文件 | 改动内容 | 预期效果 |
|---|---|---|---|
| 段落跳过过滤 | `pipeline.py` | 新增 `_should_skip_para()`：极短/纯英文/参考文献行不发 AI | 减少30~50% AI 调用次数 |
| 并发数提升 | `pipeline.py` | `Semaphore(8)` → `Semaphore(16)` | 吞吐量翻倍 |
| AI 超时缩短 | `ai_client.py` | 默认 `timeout=60s→20s`，`retries=2→1` | 最坏卡顿 240s→40s |
| 模板写盘异步 | `template_manager.py` | 使用次数写 JSON 改为后台 daemon 线程 | 格式化不阻塞主流程 |
| Celery 真并发 | `celery_app.py` | `worker_pool=solo→threads` | 开启真正多线程 |

### v1.0 Bug 修复记录

| Fix | 文件 | 问题描述 | 修复方式 |
|---|---|---|---|
| fix1 | `pipeline.py` | 全清重建导致段落结构串位 | 原位替换：找到第一个 w:r 锚点后插入修订节点 |
| fix2 | `pipeline.py` | 双层 Semaphore 竞争；短段落不必要分块 | 移除内层 Semaphore；≤800字整段调用 |
| fix3 | `pipeline.py` | 空文件/损坏文件导致前端永久 pending | 提前检测文件有效性，立即返回错误 |
| fix4 | `chunk.py` | 格式空格被 AI 当错误删除 | 保护全角空格和连续半角空格 |
| fix5 | `chunk.py` | 参考文献 `[1]` 前置空格被误删 | 引用编号保护改为匹配前置空格 |
| fix6 | `chunk.py` | 占位符紧邻空格被 AI 误删 | 二次保护：占位符紧邻空格并入占位符 |

---

## 12. 已知问题与待解决项

### 🔴 高优先级

**问题1：多 run 段落校对后 run 独立样式丢失**

- **现象**：段落内部分文字有独立格式（局部加粗/斜体/特殊字体/颜色），校对后全部统一为第一个 run 的样式
- **根因**：`_get_rpr()` 只取第一个 run 的 `w:rPr`；`_get_para_text()` 把所有 run 拼为一个字符串，丢失了各 run 边界；`_write_revision()` 重建时用同一 `rpr_elem` 覆盖全部节点
- **影响范围**：含多种格式的段落（学术论文中较普遍）
- **待解决**：重构 `_get_para_text` 同时返回 `(text, run_spans)`，`_write_revision` 按 run 边界分段应用各自 `rpr_elem`

**问题2：`style_applicator.py` 中 `para.text =` 赋值覆写段落**

- **现象**：格式化时自动添加章节编号（"第1章 引言"），使用 `para.text = ...`，会清空段落所有 run 和格式，还原成无格式纯文本
- **根因**：`python-docx` 的 `paragraph.text =` 底层清空所有 run 后重建
- **影响范围**：`_apply_numbering` 中三处 `para.text = ...`（chapter/section_1/section_2）
- **待解决**：改为 `para.runs[0].text = ...` 或先 `clear()` 再按原 run 样式重建

---

### 🟡 中优先级

**问题3：超长段落分块时占位符可能被切断**

- **现象**：`paginate_chunks` 按句末标点切块，`__PROTxxxxxx_0000__` 若在切割边界被分到两个 chunk，`restore_terms` 找不到完整 token，该专有词丢失
- **影响范围**：正文超过 800 字的超长段落（概率性，与句子分布相关）
- **待解决**：分块时检测占位符边界，确保完整占位符不跨 chunk

**问题4：评价正文截断 30000 字**

- **现象**：超长论文（>约20页）后半部分不参与评价，评价结果偏差
- **待解决**：按章节分段评价后合并，或使用支持长上下文的模型

---

### 🟢 低优先级

**问题5：`storage/` 无自动清理**

- Redis 结果24小时后自动过期，但磁盘文件无清理机制，长期运行会占满磁盘
- **待解决**：添加定时任务（Celery Beat 或 APScheduler）定期清理过期文件

**问题6：模板 `usage_count` 并发写冲突**

- 多并发时多个后台线程同时写同一 JSON，存在 last-write-wins 覆盖
- **影响**：使用次数统计不准确（非核心功能，可接受）

---

## 13. 部署说明

### 13.1 依赖服务

| 服务 | 用途 | 默认地址 |
|---|---|---|
| Redis | Celery Broker + Result Backend | localhost:6379 |
| 百炼 API | 主力 AI 服务 | dashscope.aliyuncs.com |
| DeepSeek API | 备用 AI 服务 | api.deepseek.com |

### 13.2 本地开发启动

```bash
# 1. 启动 Redis
redis-server

# 2. 进入项目，激活虚拟环境
cd pdf_check
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# 3. 启动 FastAPI（终端1）
cd backend
uvicorn app.main:app --reload --port 8000

# 4. 启动 Celery Worker（终端2）
cd backend
celery -A app.workers.celery_app worker --loglevel=info -Q proofread,evaluation,formatter,default

# 5. 启动前端（终端3）
cd frontend
npm run dev
```

### 13.3 CORS 常见问题

Vite 默认端口 5173，被占用时自动切换到 5174。两个端口必须都在 `CORS_ORIGINS` 中，否则 OPTIONS 预检返回 400。

**推荐固定端口（`vite.config.js`）：**
```javascript
server: {
  port: 5173,
  strictPort: true   // 端口被占用时报错，而非自动切换
}
```

### 13.4 Docker 部署

```bash
cd backend
docker build -t paper-checker .
docker run -p 8000:8000 \
  -e BAILIAN_API_KEY=xxx \
  -e REDIS_HOST=redis \
  paper-checker
```

---

## 14. 后续迭代规划

### 近期（v1.3）— Bug 修复

- [ ] 修复多 run 段落校对后格式丢失（`pipeline.py` `_write_revision` 重构）
- [ ] 修复 `style_applicator.py` `para.text =` 赋值格式覆盖问题
- [ ] 修复超长段落分块时占位符被切断
- [ ] 添加 `storage/` 定时清理任务（Celery Beat）

### 中期（v2.0）— 功能扩展

- [ ] 用户认证系统（JWT，复用 `models/user.py`）
- [ ] 任务历史记录持久化（PostgreSQL，复用 `models/task.py`）
- [ ] 支持 `.pdf` 格式输入（先转 `.docx` 再处理）
- [ ] 评价支持超长论文（分章节评价 + 合并）
- [ ] `cache_service.py` + `task_service.py` 完整实现
- [ ] 模板库扩充（完善 `generate_templates.py`）

### 长期（v3.0）— 架构升级

- [ ] WebSocket 实时推送进度（替代前端轮询）
- [ ] 多文件批量处理队列
- [ ] 评价结果版本管理（同一论文多次评价对比）
- [ ] 私有化部署模型支持（Ollama/本地 LLM）
- [ ] 柱状图生成接口（`chart_generator.py` 已实现 `generate_bar_chart`，待接入）
