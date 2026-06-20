# CLAUDE-MAP.md — 论文评价检验系统 代码地图

本文档面向 Claude Code / 后续开发者，描述本仓库当前（2026-06）的真实目录结构与功能逻辑。
与 `CLAUDE.md`（项目规范/开发命令）不同，本文档聚焦于**代码实际长成什么样**——已经远超 PRD 最初设定的"评价+校对+排版"三件套，新增了**查重（中英文）、用户认证（账号/短信/微信/支付宝）、计费与订单、管理后台、本地论文库（FAISS）**等完整子系统。

---

## 1. 项目总览

| 维度 | 说明 |
|---|---|
| 形态 | FastAPI 后端 + Vue3/Vite 前端 + Celery/Redis 异步任务 + MySQL/SQLite |
| 四大业务功能 | ① 智能评价 evaluation ② 论文校对 proofread ③ 模板排版 formatter ④ 论文查重 plagiarism |
| 配套体系 | 用户认证 auth、计费订单 billing、管理后台 admin、本地论文库 admin_papers |
| AI 能力 | 统一 `ai_client.py`：阿里百炼(通义千问) 优先，DeepSeek 兜底；查重模块额外用 sentence-transformers 做语义编码 |
| 任务模型 | 4 类 Celery 任务（evaluation/proofread/formatter/plagiarism），各自独立队列，前端轮询 status 接口 |

---

## 2. 目录结构

```
pdf_check/
├── backend/                              # FastAPI 后端
│   ├── app/
│   │   ├── main.py                       # FastAPI 入口：lifespan、CORS、全局异常处理、/health
│   │   ├── config.py                     # Pydantic Settings：AI Key、DB、Redis、Celery、支付、查重参数等
│   │   │
│   │   ├── api/v1/
│   │   │   ├── router.py                 # 汇总 8 个子路由，逐个 try/except 容错加载
│   │   │   ├── deps.py                   # require_quota() 配额依赖注入
│   │   │   ├── evaluation.py             # POST /evaluation/upload 等 4 个接口
│   │   │   ├── proofread.py              # POST /proofread/upload 等 4 个接口
│   │   │   ├── formatter.py              # POST /formatter/format + 模板 CRUD，共 10 个接口
│   │   │   ├── plagiarism.py             # POST /plagiarism/upload 等 4 个接口
│   │   │   ├── auth.py                   # 账号/短信/微信/支付宝登录 + 管理员审批，约 14 个接口
│   │   │   ├── admin.py                  # 系统配置、用户、订单、退款审批，约 10 个接口
│   │   │   ├── admin_papers.py           # 本地论文库 CRUD + FAISS 重建，5 个接口
│   │   │   └── billing.py                # 定价/配额/下单/支付回调/邀请码，约 11 个接口
│   │   │
│   │   ├── core/                         # 核心业务逻辑（无 HTTP/Celery 依赖，纯逻辑）
│   │   │   ├── ai_client.py              # 统一 LLM 调用：call_ai()/call_ai_sync()，百炼→DeepSeek 自动降级重试
│   │   │   │
│   │   │   ├── evaluator/                # 【智能评价】
│   │   │   │   ├── prompts.py            #   5 维度权重 + 按论文类型(文/理工/艺术)差异化 prompt
│   │   │   │   ├── report_generator.py   #   生成 Word 报告（含雷达图、问题汇总）
│   │   │   │   └── chart_generator.py    #   生成雷达图
│   │   │   │
│   │   │   ├── formatter/                # 【模板排版】
│   │   │   │   ├── format_engine.py      #   主流程：解析→匹配模板→ZIP 级样式注入
│   │   │   │   ├── structure_analyzer.py #   关键词/编号/样式三重识别文档分区(SectionType)
│   │   │   │   ├── style_applicator.py   #   样式落地
│   │   │   │   └── template_manager.py   #   模板元数据/配置 CRUD
│   │   │   │
│   │   │   ├── proofreadme/              # 【论文校对】
│   │   │   │   ├── pipeline.py           #   process_word_sync()：段落级 AI 校对 + Track Changes 写入
│   │   │   │   ├── llm.py                #   三段式 prompt：拼写/语法/段落逻辑
│   │   │   │   ├── chunk.py              #   protect_terms/restore_terms（占位符保护专有名词）
│   │   │   │   ├── diff_engine.py        #   compute_diff() 计算改动片段
│   │   │   │   └── word_patch.py         #   w:del/w:ins 修订标记节点构造
│   │   │   │
│   │   │   └── plagiarism/               # 【论文查重】— 全仓库最复杂的子系统，见 §3.5 详述
│   │   │       ├── base_checker.py / checker_context.py / levels.py
│   │   │       ├── language_detector.py / text_parser.py / reference_stripper.py
│   │   │       ├── semantic_encoder.py / ngram_matcher.py / key_sentence_extractor.py
│   │   │       ├── confidence_scorer.py / local_index.py
│   │   │       ├── prompts.py / prompts_en.py / report_generator.py
│   │   │       ├── engines/   { opensource_checker, hybrid_checker, english_academic_checker }
│   │   │       └── external/  { aggregator, base_source, core_api, pubmed, semantic_scholar }
│   │   │
│   │   ├── models/                       # SQLAlchemy ORM
│   │   │   ├── user.py                   #   User 表 + init_db()（自动建表/建管理员）
│   │   │   ├── billing.py                #   SystemConfig/Subscription/QuotaBalance/Order/UsageRecord/TaskRecord/InviteCode
│   │   │   ├── local_paper.py            #   LocalPaper（查重本地库，含 384 维向量 BLOB）
│   │   │   ├── task.py / pricing.py
│   │   │
│   │   ├── schemas/                      # Pydantic 请求/响应模型
│   │   │   ├── evaluation.py / billing.py / formatting.py / spell_check.py
│   │   │
│   │   ├── services/                     # 业务服务层（被 api/ 和 workers/ 共同调用）
│   │   │   ├── file_service.py           #   保存/校验/清理上传文件
│   │   │   ├── task_store.py             #   Celery 结果 → MySQL 兜底持久化（Redis 7 天过期）
│   │   │   ├── billing_service.py        #   配额检查/扣减、下单、支付确认、退款、邀请码
│   │   │   ├── docx_normalizer.py        #   WPS 文档 → LibreOffice 转标准 docx
│   │   │   ├── pdf_extractor.py          #   pdfplumber 提取 PDF 文本
│   │   │   ├── oauth_service.py          #   微信/支付宝 OAuth 换 token
│   │   │   ├── payment_service.py        #   微信支付/支付宝下单、签名校验、退款
│   │   │   ├── sms_service.py            #   阿里云短信验证码
│   │   │   └── cache_service.py          #   Redis 封装
│   │   │
│   │   ├── workers/                      # Celery 异步任务（4 个独立队列）
│   │   │   ├── celery_app.py             #   Redis broker、队列路由、并发 128、软/硬超时 540s/600s
│   │   │   ├── evaluation_tasks.py       #   run_evaluation：5 维度并发 AI 评分 + 后置合规性检查
│   │   │   ├── proofread_tasks.py        #   run_proofread：调用 pipeline.process_word_sync()
│   │   │   ├── formatter_tasks.py        #   run_formatting：调用 FormatEngine.format_document()
│   │   │   └── plagiarism_tasks.py       #   run_plagiarism_check：语言路由 + 中/英文检测引擎调度
│   │   │
│   │   └── utils/                        # exceptions.py / file_utils.py / logger.py
│   │
│   ├── templates/
│   │   ├── builtin/                      # 内置模板：浙大/清华毕业论文、中文核心期刊投稿（各配 .docx+.json）
│   │   └── user/custom/                  # 用户上传的自定义模板
│   ├── storage/                          # uploads/outputs/temp/proofread/formatter/plagiarism/wechat/alipay
│   ├── scripts/                          # ingest_openalex.py（论文库导入）、poc_style_injection.py
│   ├── tests/                            # pytest：test_billing.py + test_plagiarism_english/（5 个单测文件）
│   └── 根目录脚本                          # init_db.py / migrate_db.py / check_services.py / start_celery_worker.py 等运维脚本
│
├── frontend/                              # Vue3 + Vite + Element Plus + Pinia + ECharts
│   └── src/
│       ├── main.js                       # 挂载 Pinia/Router/Element Plus/ECharts 到 #app
│       ├── App.vue                       # 顶部导航 + 30s 轮询用户状态 + router-view
│       ├── router/index.js               # 11 条路由 + beforeEach 鉴权守卫
│       ├── store/                        # Pinia（自定义 localStorage 持久化插件）
│       │   ├── index.js                  #   持久化插件：自动存取 localStorage，plagiarism 特殊重置逻辑
│       │   └── modules/                  #   auth/billing/evaluation/formatting/spellCheck/plagiarism/history/task/user
│       ├── api/                          # axios 封装，每个业务一个文件，与后端路由一一对应
│       │   ├── index.js                  #   请求/响应拦截器：token 注入、402 弹窗、5xx 自动重试、超时分级
│       │   └── auth/billing/evaluation/formatting/plagiarism/spellCheck/admin.js
│       ├── views/                        # Home/Login/Evaluation/SpellCheck/Formatting/Plagiarism/History/Pricing/UserCenter/Admin/WechatCallback
│       ├── components/
│       │   ├── charts/                   #   RadarChart/BarChart/TrendChart（ECharts 封装）
│       │   ├── common/                   #   FileUpload/LoadingSpinner/Footer
│       │   ├── evaluation/               #   ScoreCard
│       │   ├── plagiarism/               #   SourceCardCn/SourceCardEn/ProgressStages/CopyDoiList/ReportExporter/FallbackBanner
│       │   ├── icons/                    #   4 个业务图标
│       │   └── （根目录下 FileUpload/ProgressBar/ResultCard/RadarChart.vue 为早期遗留版本，已被 common/charts 下同名组件取代）
│       └── utils/                        # storage.js(localStorage 封装) / fileUtils.js(校验/格式化) / chartConfig.js(ECharts option 生成) / request.js
│
├── docker/                                # docker-compose.yml + nginx.conf + redis.conf
├── database/                              # init.sql + migrations/
├── docs/                                  # API文档.md / 部署指南.md
├── scripts/                               # clean_files.sh / init_db.sh
└── 根目录历史文档                           # *.md 调试报告、需求文档(*.md/*.pdf)、backend.rar 等——产品历史记录，非当前源码逻辑
```

---

## 3. 后端功能逻辑详解

### 3.1 入口与配置

- **`backend/app/main.py`**：`lifespan()` 启动时调用 `models.user.init_db()` 建表/建管理员账号；注册全局异常处理器（兜底返回 500 JSON）；`/` 和 `/health` 暴露版本与 API Key 配置状态；CORS 来源读 `config.CORS_ORIGINS`；日志同时输出到 stdout 和按天滚动的文件。
- **`backend/app/config.py`**：Pydantic v2 `Settings`，涵盖 AI（百炼/DeepSeek 双模型配置）、JWT（7 天过期）、Celery/Redis、微信/支付宝支付与登录凭证、阿里云短信、查重外部 API（Semantic Scholar/CORE/PubMed）及查重算法参数（embedding 阈值、ngram 窗口、最低置信度，按论文类型分层）。`_build_storage_paths()` 校验器自动创建所有 storage 子目录。
- **`backend/app/api/v1/router.py`**：依次加载 8 个子路由，每个用 try/except 包裹并打印 ✅/❌，单个子模块加载失败不影响其余路由可用。
- **`backend/app/api/v1/deps.py`**：`require_quota(action)` 依赖注入——计费关闭时直接放行；开启时调用 `billing_service.check_quota()`，配额不足抛 HTTP 402。

### 3.2 API 端点

#### evaluation.py — 智能评价
| 路径 | 方法 | 说明 |
|---|---|---|
| `/upload` | POST | 上传 docx/pdf，提取标题与结构化内容（摘要/关键词/大纲/结论/参考文献），提交 `run_evaluation` 任务 |
| `/status/{task_id}` | GET | 轮询 Celery 状态 |
| `/result/{task_id}` | GET | 取完整评价结果 |
| `/download/{report_id}` | GET | 下载 Word 评价报告 |

文档结构提取（`_extract_structure`）用状态机解析 preamble→abstract→body→references，PDF 解析失败时有正则兜底（`_extract_structure_from_text`）。

#### proofread.py — 论文校对
`/upload`（保存为 `{task_id}_in.docx`，提交 `run_proofread`）、`/status/{task_id}`（Redis 优先，过期回落 MySQL `task_store`）、`/download/{task_id}`、`DELETE /task/{task_id}`（仅 PENDING/STARTED 可撤销）。

#### formatter.py — 模板排版
两步式自定义模板上传：`/templates/analyze`（临时校验+生成风格摘要）→`/templates/confirm`（落盘）；另有 `/format`、`/templates`（列表）、`/status/{task_id}`、`/download/{task_id}`、`/preview`（仅结构预览不提交任务）、模板删除接口。

#### plagiarism.py — 论文查重
`/config`（返回英文查重是否开启等前端开关）、`/upload`（语言 auto/zh/en，**英文消耗 2 配额，中文 1 配额**，下单前预检配额）、`/status/{task_id}`（含 stage 阶段名）、`/report/{task_id}`。

#### auth.py — 认证（约 14 个接口）
账号密码登录/注册（注册后默认 `is_approved=False`，需管理员审批）、JWT 签发与解析、管理员创建/审批/驳回/恢复用户、短信验证码登录（首次登录自动建号+应用邀请码）、微信/支付宝 OAuth（state 参数携带邀请码，回调按 openid/uid 自动建号或登录）。

#### admin.py / admin_papers.py — 管理后台
系统配置读写、用户列表（含订阅与配额汇总）、近 7 日活跃用户数统计、手动授予配额、订单列表、退款审批/驳回（调用对应支付网关退款接口）；`admin_papers.py` 管理查重本地论文库：统计、分页列表（关键词/来源/年份/是否有向量过滤）、详情、删除（同步从 FAISS 移除）、`/rebuild` 全量重建索引。

#### billing.py — 计费
定价查询、我的配额、创建订单（生成微信/支付宝支付链接）、订单列表/状态、申请退款、微信/支付宝**支付回调**（签名校验→`confirm_payment()`）、用量记录、邀请码生成与查询。

### 3.3 Celery 异步任务

- **`celery_app.py`**：Redis 作 broker+backend，JSON 序列化，结果保留 7 天；4 个任务模块各路由到独立队列（proofread/evaluation/formatter/plagiarism）；`worker_concurrency=128`（线程池，适配 IO 密集型 AI 调用）；`worker_prefetch_multiplier=1` + `task_acks_late=True`，保证长任务不被预取打断、worker 崩溃后任务可重新投递；软超时 540s / 硬超时 600s。
- **`evaluation_tasks.run_evaluation`**：`_evaluate_all_dimensions()` 用 `asyncio.gather()` 并发调用 5 个维度的 AI 评分，解析失败有兜底响应；按维度权重算加权总分；额外有非阻塞的 `_run_integrity_check()`（学术诚信风险检查）。
- **`proofread_tasks.run_proofread`**：更新 PROGRESS 状态 → 调 `pipeline.process_word_sync(in_path, out_path, mode)` → 结果同时写 Redis（Celery 默认）与 MySQL（`task_store.save_task_result`，供 Redis 过期后兜底查询）。
- **`formatter_tasks.run_formatting`**：懒加载全局单例 `FormatEngine`，调用 `format_document(..., progress_cb=_progress)`，进度回调实时更新 Celery state 的 stage 文案。
- **`plagiarism_tasks.run_plagiarism_check`**：解析文件→（auto 时）语言检测→按语言路由到 `HybridChecker`（中文）或 `EnglishAcademicChecker`（英文，外部 API 全部失败时**自动降级回 HybridChecker**）→`enrich_report()`补充改写建议/期刊意见。中文阶段划分 5%/20%/80%/90%，英文划分 5%/15%/25%/40%/55%/65%/80%/95%（8 阶段，对应本地检索/Scholar/CORE/PubMed/AI 验证等步骤）。

### 3.4 核心业务模块

- **`ai_client.py`**：模型池 `[("百炼/千问", _call_qwen), ("DeepSeek", _call_deepseek)]`，`call_ai()` 按模型顺序重试，全部失败抛 `RuntimeError`；`parse_json_response()` 兼容剥离 Markdown 代码块围栏，解析失败返回调用方提供的 fallback 字典。
- **evaluator**：5 维度（选题意义/写作安排/逻辑构建/专业能力/学术规范，权重 10/10/20/40/20）按论文类型（人文/理工/艺术）差异化措辞；`report_generator.py` 产出含雷达图、维度评分表、问题汇总的 Word 报告。
- **formatter**：`StructureAnalyzer` 用关键词→编号模式→样式→（可选）AI 四级优先级识别 16 种 `SectionType`；`FormatEngine` 在 ZIP 层面替换 `styles.xml`/`theme1.xml`，并对 `numbering.xml` 做合并（保留用户原有编号、追加模板编号定义）；`TemplateManager` 负责模板元数据 CRUD，内置模板不可删除。
- **proofreadme**：`pipeline.process_word_sync()` 逐段落跳过图片/表格等不可校对内容，用 Semaphore(16) 并发调 AI（拼写→语法→段落逻辑三段式 prompt，见 `llm.py`），再串行写回 Word Track Changes（`word_patch.py` 构造 `w:del`/`w:ins` 节点）；`chunk.py` 用占位符 `__PROTxxxxxx_0000__` 保护专有名词/公式不被改写。

### 3.5 查重子系统（plagiarism）— 详细管线

这是仓库内最复杂的模块，采用"语言检测 → 引擎路由 → 多源证据融合 → 置信度打分 → 分级建议"的整体设计。

**基础设施**
- `levels.py`：按论文类型（本科/硕士/博士/期刊）× 语言（中/英）维护差异化阈值表（高危/中危比例、确认阈值、严格度、是否生成改写建议）。`classify_risk()` 据此判级，`get_threshold_snapshot()` 把当次判级用的阈值原样存入报告供前端展示。
- `base_checker.py`：定义 `HighlightItem`/`SourceItem`/`CheckSummary`/`CheckResult` 数据结构及 `BaseChecker` 抽象接口，所有引擎统一产出格式。
- `checker_context.py`：单例工厂 `get_checker(language)`——英文固定走 `EnglishAcademicChecker`；中文默认 `HybridChecker`，环境变量 `PLAGIARISM_ENGINE=opensource` 可切到 `OpenSourceChecker`。

**预处理**
- `language_detector.py`：`langdetect`（固定种子保证可复现）+ 中文字符占比兜底，输出 zh/en。
- `text_parser.py`：docx/pdf/txt 统一解析为纯文本，并做句子切分（依据中英文标点，控制句长 20–150 字）。
- `reference_stripper.py`（仅英文）：剥离 References/Bibliography 章节标题及正文中 `[12]`、`(Smith, 2020)` 等引文标记，避免参考文献本身被误判抄袭。

**核心算法组件**
- `semantic_encoder.py`：`sentence-transformers/all-MiniLM-L6-v2`（384 维，懒加载单例），`cosine_topk()` 矩阵乘法求 topK 相似候选。
- `ngram_matcher.py`：n-gram（默认 6 词窗口）逐句扫描，命中即判定"直接抄袭"（置信度 95，跳过 AI 复核，节省成本）。
- `key_sentence_extractor.py`（英文）：启发式打分（定义句/数据句加分，引文残留/疑问句减分）抽取代表性句子，按引言/方法结果/结论三段配额分布。
- `confidence_scorer.py`：综合 ngram 命中(+50)、embedding 相似度区间(+10~+30)、AI 判定结果(direct_copy +30 / paraphrase +20 / common_knowledge +5 / original −20)，clamp 到 0–100。
- `local_index.py`：FAISS（IndexIDMap/IndexFlatIP，384 维）作为 MySQL `LocalPaper` 表之上的向量检索加速层，支持增量增删与全量重建，结果数 ≥100 时自动从 DB 重建。

**三个检测引擎**
1. `opensource_checker.py`：SimHash 粗筛 + TF-IDF 精筛的离线兜底方案，不依赖外部 API/AI，速度最快但精度有限，内置 3 篇演示语料。
2. `hybrid_checker.py`（中文主引擎）：纯 LLM 驱动——400 字分块(50 字重叠)→qwen-turbo 批量初筛(8/批,4 并发)→按论文类型阈值筛出候选→qwen-plus 深度确认(最多 8 块,4 并发)→区间合并算重复率→`classify_risk`判级。
3. `english_academic_checker.py`（英文主引擎）：剥离引用→抽取关键句→本地 FAISS 检索（命中数 <5 时触发外部 API）→`ExternalSourceAggregator` 并发查询 Semantic Scholar/CORE/PubMed（去重、限流、Redis 7 天缓存，三源全失败时抛 `ExternalSourceAggregatorAllFailedError` 触发上层降级）→候选库整体编码→cosine topK→逐对 n-gram 检测（命中跳过 AI）→剩余对批量丢给 qwen-plus 判定→按 `min_confidence` 过滤→**异步回写**新候选论文到本地库（MySQL+FAISS，不阻塞主流程）。

**外部数据源**（`external/`）：`aggregator.py` 并发调度三个 `ExternalSource` 子类（`semantic_scholar.py`/`core_api.py`/`pubmed.py`），各自实现 `_do_search()`，统一走 `base_source.py` 的缓存+限流+重试模板方法；按 DOI 或标准化标题去重；只要有一个源成功就不算整体失败。

**后处理**：`report_generator.enrich_report()` 仅对博士/期刊档位触发——对 Top5 高相似片段并发请求 LLM 生成改写建议，期刊档位额外生成总体投稿意见，全程非阻塞（LLM 失败仅记 WARNING，报告仍正常返回）。

**与外层的连接**：由 `workers/plagiarism_tasks.py` 编排整条管线并上报阶段进度；产物经 `api/v1/plagiarism.py` 序列化为 JSON 返回前端；查重结果同时受 `models/billing.py` 的 `QuotaBalance` 约束（中文 1 配额、英文 2 配额）。

### 3.6 数据模型

**ORM (models/)**
- `User`：账号/邮箱/手机号/微信 openid/支付宝 uid 多种身份字段并存，`invited_by` 自引用外键记录邀请关系；`init_db()` 启动时强制重置管理员密码（admin/admin123）以保证可登录。
- `billing.py`：`SystemConfig`(KV配置)、`Subscription`(包月)、`QuotaBalance`(按来源 free/purchase/referral/subscription 分桶,唯一约束 user+source)、`Order`(订单+退款全生命周期字段)、`UsageRecord`(用量审计)、`TaskRecord`(Celery 结果的 MySQL 兜底)、`InviteCode`(邀请码)。
- `local_paper.py`：`LocalPaper`，`embedding` 为 `LargeBinary`（384×float32=1536 字节），唯一约束 doi/title_hash。

**Pydantic (schemas/)**：`evaluation.py`(EvaluationResult/EvaluationResponse)、`billing.py`(OrderCreate/OrderOut/QuotaResponse/SystemConfigUpdate/InviteCodeOut/UsageRecordOut)、`formatting.py`(FormatRequest/FormatStatusResponse)。

### 3.7 服务层

| 文件 | 职责 |
|---|---|
| `file_service.py` | 保存上传文件（UUID 防冲突）、类型/大小校验、按 `FILE_RETENTION_HOURS` 清理旧文件 |
| `task_store.py` | Celery 结果双写 MySQL（Redis 7 天过期后的兜底来源） |
| `billing_service.py` | 配额检查优先级 admin>subscription>purchase>referral>free；`consume_quota()` 用原生 SQL UPDATE 保证并发扣减原子性；订单创建/支付确认/退款申请-审批-驳回；邀请码生成与核销 |
| `docx_normalizer.py` | 检测 WPS 生成的非标准 docx，调用本机 LibreOffice(`soffice --headless`) 转标准格式；soffice 不可用时优雅退回原文件 |
| `pdf_extractor.py` | `pdfplumber` 按词提取并拼接文本，过滤控制字符，<50 字符判定为扫描版/空文档并抛错 |
| `oauth_service.py` / `payment_service.py` / `sms_service.py` / `cache_service.py` | 微信/支付宝 OAuth 换 token；微信支付/支付宝下单与签名校验与退款；阿里云短信验证码；Redis 封装 |

### 3.8 工具层（utils/）

`exceptions.py`（自定义异常类）、`file_utils.py`（`clean_old_files()`）、`logger.py`（loguru 配置：终端彩色 + 按天滚动文件，30 天保留）。

---

## 4. 前端功能逻辑详解

### 4.1 入口与路由

`main.js` 挂载 Pinia + Router + Element Plus(+图标) + ECharts(雷达/柱状/折线) 到 `#app`。`App.vue` 固定顶部导航（首页/智能评价/校对/排版/查重），登录态显示用户下拉菜单，每 30 秒调 `authStore.fetchMe()` 检测账号是否被禁用，`router-view` 带淡入过渡。

`router/index.js` 11 条路由，`/evaluation`、`/spell-check`、`/formatting`、`/plagiarism`、`/history`、`/admin`、`/user-center` 需登录；`beforeEach` 守卫检查 `localStorage.access_token`，未登录跳转 `/login?redirect=原路径`。

### 4.2 状态管理（Pinia，自定义 localStorage 持久化）

`store/index.js` 的持久化插件会在每次 mutation 后自动把 state 写入 `localStorage`（key: `pinia-{store.$id}`），并在初始化时还原；**特例**：plagiarism store 若上次状态停留在 pending/processing/uploading/partial（页面刷新打断了轮询），加载时会重置，避免卡死在过期状态；`pendingResult` 字段不持久化（仅用于"从历史记录跳转查看"的会话内传值）。

| Store | 状态机/核心字段 | 对应后端 |
|---|---|---|
| `auth.js` | token/user；`isLoggedIn/isAdmin/isApproved` | `/auth/login` `/auth/me` |
| `billing.js` | pricing/quota/orders/inviteCodes/usageHistory | `/billing/*` |
| `evaluation.js` | idle→uploading→processing→completed\|failed；2s 轮询，5 分钟超时，3 次网络重试 | `/evaluation/*` |
| `formatting.js` | idle→processing→completed\|failed；3s 轮询 | `/formatter/*` |
| `spellCheck.js` | idle→processing→completed\|failed；3s 轮询 | `/proofread/*` |
| `plagiarism.js` | idle→uploading→pending→partial→done\|failed；2s 轮询；`activeTab`(zh/en) 区分中英文查重 | `/plagiarism/*` |
| `history.js` | 纯前端 localStorage 记录列表（最多 100 条），按类型/日期过滤 | 无后端调用 |

各 `*Action` 均遵循「上传拿 task_id → 轮询 status → 完成后取结果/报告 → 写入 history」的统一模式；`resumeIfProcessing()` 用于页面刷新后恢复未完成的轮询，`loadPendingOrKeep()`/`setPendingResult()` 用于"历史记录→点击查看→跳回功能页"的结果回填。

### 4.3 API 层

`api/index.js`：上传类接口超时 120s，`/status/` 轮询接口 8s，其余默认 30s；请求拦截器自动注入 `Authorization: Bearer`；响应拦截器统一解包 `response.data`，**402 配额不足**弹出对话框引导跳转 `/pricing`，5xx/超时自动重试最多 2 次（1s/2s 退避），`/status/` 轮询失败不弹错误提示（避免轮询期间打扰用户）。其余 `api/*.js`（auth/billing/evaluation/formatting/plagiarism/spellCheck/admin）均为按后端路由一一对应的函数封装，函数名与后端路径语义一致。

### 4.4 页面（views/）

- **Home.vue**：纯展示型营销首页（功能卡片、统计数字、定价对比、安全承诺），无异步状态机。
- **Login.vue**：短信验证码登录（默认）+ 微信 OAuth + 可折叠的账号密码登录（管理员用），支持邀请码、`redirect` 回跳。
- **Evaluation.vue**：选论文类型→上传→轮询→完成后展示总分/雷达图+柱状图/5 张维度卡（优点/不足/建议）→下载报告；从历史记录跳转时会还原 `pendingResult`。
- **SpellCheck.vue**：上传 docx→轮询→展示检查/修改/跳过统计→下载带 Word 修订标记的文件。
- **Formatting.vue**：先选模板（内置/自定义，自定义模板可删除）→上传→轮询→展示格式化分区数与耗时→下载；自定义模板上传走"分析(临时)→确认(落盘)"两步。
- **Plagiarism.vue**：中/英文双 Tab（英文 Tab 受 `englishCheckEnabled` 开关控制），分别选论文档位→上传→8 阶段进度条→展示相似度/风险等级/来源卡片（中文 SourceCardCn / 英文 SourceCardEn 含 DOI）。
- **History.vue**：按类型/日期过滤本地历史记录，支持跳转回原功能页查看详情或删除/清空。
- **Pricing.vue / UserCenter.vue**：定价展示+下单（微信/支付宝二选一）；个人中心查看配额余额、订阅有效期、邀请码、用量明细。
- **Admin.vue**：用户管理（创建/审批/授予配额）、订单管理、退款审批、（如启用）本地论文库管理。
- **WechatCallback.vue**：解析 OAuth 回调 code，换 token 后调 `authStore.loginWithToken()` 并跳转。

### 4.5 组件（components/）

- `charts/`：RadarChart（评价 5 维度）、BarChart（维度对比）、TrendChart（历史趋势）——均封装 `chartConfig.js` 生成的 ECharts option。
- `common/`：FileUpload（拖拽/点击上传+校验+进度条）、LoadingSpinner、Footer。
- `evaluation/ScoreCard.vue`：单维度评分卡（优点/不足/建议三段式）。
- `plagiarism/`：SourceCardCn/En（来源匹配卡片）、ProgressStages（8 阶段进度可视化）、CopyDoiList（DOI 列表复制）、ReportExporter（报告导出）、FallbackBanner（降级提示横幅）。
- `icons/`：四个业务图标组件。
- 根目录下的 `FileUpload.vue`/`ProgressBar.vue`/`ResultCard.vue`/`RadarChart.vue` 为早期版本，功能已被 `common/` 与 `charts/` 下同名组件取代，新代码不应再引用。

### 4.6 工具函数（utils/）

`storage.js`（带 `paper_check_` 前缀的 localStorage 读写，含容量溢出兜底）、`fileUtils.js`（`validateFile`/`formatFileSize`/`getFileExtension`）、`chartConfig.js`（雷达图固定 5 维度、柱状图按输入动态维度、趋势图折线+面积，统一主题色 `#006C49`）。

---

## 5. 端到端数据流

### 5.1 智能评价
```
上传 docx/pdf + paper_type
  → 后端提取标题/摘要/关键词/大纲/结论/参考文献
  → run_evaluation：5 维度并发调 AI（百炼→DeepSeek 降级）→ 加权总分
  → 生成 Word 报告（含雷达图）
  → 前端 2s 轮询 status → completed 后取 result → 展示图表+维度卡 → 下载报告
```

### 5.2 论文校对
```
上传 docx
  → run_proofread：WPS 文档归一化 → 逐段落 16 并发 AI 校对（拼写/语法/段落逻辑）
  → 计算 diff → 串行写回 Word Track Changes
  → 结果双写 Redis + MySQL
  → 前端 3s 轮询 → 展示检查/修改统计 → 下载修订版
```

### 5.3 模板排版
```
选模板 + 上传 docx
  → run_formatting：解析文档结构 → 加载模板 → ZIP 级样式注入(styles.xml/theme1.xml 替换，numbering.xml 合并)
  → 前端 3s 轮询 → 展示分区数/耗时 → 下载
```

### 5.4 论文查重
```
上传文件 + 语言(auto/zh/en) + 论文档位
  → 预检配额(中文1/英文2) → 提交 run_plagiarism_check
  → 语言检测(auto时) → 路由：
       中文 → HybridChecker(分块→turbo初筛→plus深度确认)
       英文 → EnglishAcademicChecker(本地FAISS→外部API聚合→ngram→AI批量验证)，外部API全失败则降级回 HybridChecker
  → enrich_report()（博士/期刊档位追加改写建议/投稿意见）
  → 前端 2s 轮询 8 阶段进度 → 展示相似度/风险等级/来源卡片
```

### 5.5 认证与计费
```
注册/短信登录/微信登录 → ensure_free_trial() 自动发放免费额度
使用功能前 → check_quota()（优先级：管理员 > 订阅 > 购买 > 推荐 > 免费）
使用后 → consume_quota()（原生 SQL 原子扣减）+ 记录 UsageRecord
配额不足 → 前端 402 弹窗引导 /pricing → 创建订单 → 微信/支付宝下单生成支付链接
支付网关回调 → 签名校验 → confirm_payment()（包月开 Subscription，按次发 QuotaBalance）
```

---

## 6. 关键设计要点

1. **AI 双模型容灾**：所有 LLM 调用统一经 `ai_client.call_ai()`，百炼失败自动切 DeepSeek，二者都失败才抛异常——四大业务模块（评价/校对/排版可选/查重）共享同一套降级策略。
2. **结果持久化双写**：Celery 结果默认存 Redis（7 天过期），同时写 MySQL `TaskRecord`/`task_store`，避免长时间未下载导致结果丢失。
3. **配额扣减原子性**：`billing_service.consume_quota()` 用原生 SQL UPDATE（非 ORM 先读后写），避免高并发下超扣。
4. **查重的分层降级**：英文查重链路最长（本地 FAISS→3 个外部学术 API→ngram→AI），任一外部源失败不影响整体，三源全失败才整体降级回中文引擎逃生。
5. **前端轮询是核心交互范式**：四大功能 + 无一例外都是"提交任务拿 task_id → 定时轮询 status → 完成后再取详情"，前端为此在每个 store 里都实现了 resume/cancel/retry 逻辑。
6. **Token 经济换算**：评价/校对内容会被截断（标题 100 字、正文 1 万字）以控制 token 成本，查重则用分块/关键句抽取代替全文输入 LLM。
