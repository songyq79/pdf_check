# 产品需求文档：论文评价检验系统 2.0 升级计划
## 从"论文工具链"到"学位论文全流程助手"

**文档版本**: v1.0  
**最后更新**: 2026-06-18  
**负责人**: [项目负责人]  
**状态**: 规划阶段

---

## 目录

1. [执行摘要](#执行摘要)
2. [产品现状分析](#产品现状分析)
3. [战略升级目标](#战略升级目标)
4. [核心需求](#核心需求)
5. [实现路线图](#实现路线图)
6. [技术架构](#技术架构)
7. [商业预测](#商业预测)
8. [风险与对策](#风险与对策)
9. [附录](#附录)

---

## 执行摘要

### 当前状态
- **产品形态**: 学位论文"后期处理工具链"（评价→校对→排版→查重）
- **现有收入**: 50-200万/年
- **防护城河强度**: ⭐ 较弱（功能容易复制，用户易迁移）
- **核心问题**: 用户仅在论文完成后才接触本产品，前期选题、写作环节不在我们的平台

### 升级方向
将产品从"**论文后期处理工具**"升级为"**学位论文全生命周期助手**"，覆盖：
```
选题 → 文献综述 → 实验设计 → 论文写作 → 评价改进 → 校对排版 → 查重投稿
```

### 预期效果
- **收入增长**: 50-200万/年 → 200-500万+/年
- **防护城河**: ⭐ → ⭐⭐⭐⭐⭐（用户工作流深度锁定）
- **用户粘性**: 单篇论文 → 整个学位周期（2-4年）
- **高校合作**: ToC散户 → ToB机构年费合同

---

## 产品现状分析

### 现有产品形态（v1.0）

#### 四大核心功能

| 功能 | 说明 | 用户价值 | 当前定价 |
|------|------|--------|--------|
| **智能评价** | 5维度评分（选题意义/写作安排/逻辑构建/专业能力/学术规范）+ Word报告 + 雷达图 | 论文质量把关 | 50元/篇 |
| **论文校对** | AI拼写/语法/段落逻辑检查 + Word修订标记 | 文字质量提升 | 50-100元/篇 |
| **模板排版** | 套用学校/期刊规范模板，ZIP级样式注入 | 格式合规 | 30-50元/篇 |
| **论文查重** | 中英文混合查重（LLM+本地FAISS+外部API） | 学术诚实性验证 | 50-100元/篇 |

#### 配套支持系统

| 系统 | 说明 |
|------|------|
| **用户认证** | 账号/短信/微信/支付宝OAuth，管理员审批 |
| **计费系统** | 配额/订阅/按次计费，微信/支付宝支付，退款处理 |
| **管理后台** | 用户/订单/退款/本地论文库管理 |
| **数据持久化** | 双写Redis+MySQL，7天过期兜底 |

#### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + Celery/Redis |
| 前端 | Vue3 + Vite + Element Plus + ECharts |
| AI | 阿里百炼(通义千问) + DeepSeek 双模型容灾 |
| 部署 | Docker + MySQL/SQLite |

### 现有优势（护城河初期）

✅ **完整的工作流** — 评价→校对→排版→查重覆盖论文后期全过程  
✅ **生产级架构** — 异步任务、容灾、容错、双写持久化  
✅ **商业闭环** — 完整的认证、计费、支付系统  
✅ **AI容灾** — 双模型自动降级，无单点故障  
✅ **已有用户** — 存量学生用户和订阅收入  

### 现有风险（防护城河薄弱之处）

❌ **用户接触窗口短** — 仅限论文完成后期（1-3个月）  
❌ **功能可复制性强** — 提示词工程 + Web界面，3-5天可复制  
❌ **用户迁移成本低** — 单篇论文使用，无长期粘性  
❌ **前期阶段缺失** — 选题到写作（6-18个月）完全不覆盖  
❌ **竞争对手易入局** — 有足够的技术积累就能快速模仿  

---

## 战略升级目标

### 核心战略：以用户工作流深度为护城河

从"一次性交易型工具"升级到"全周期陪伴型助手"，让用户从：
```
只在论文快完成时用 → 从开题选题就开始用 → 贯穿整个学位周期
```

### 具体目标

#### 用户规模
- **Year 1**: 保持现有5-10万活跃用户，新增选题/文献功能后用户留存率从30% → 60%
- **Year 2**: 10-20万活跃用户，高校合作达到20-50所
- **Year 3**: 30-50万活跃用户，成为行业标准工具

#### 收入目标
| 时期 | ToC(学生) | ToB(高校) | 总计 |
|------|----------|----------|------|
| 现状 | 50-200万 | ~0 | 50-200万 |
| Year 1 | 100-300万 | 50-100万 | 150-400万 |
| Year 2 | 200-400万 | 300-500万 | 500-900万 |
| Year 3 | 300-500万 | 1000万+ | 1300万+ |

#### 防护城河强度
| 维度 | 现状 | 升级后 |
|------|------|--------|
| 用户工作流锁定 | ⭐ | ⭐⭐⭐⭐⭐ |
| 数据积累 | ⭐ | ⭐⭐⭐⭐ |
| 网络效应 | 无 | ⭐⭐⭐ |
| 学校关系深度 | ⭐ | ⭐⭐⭐⭐ |
| 技术难度 | ⭐⭐ | ⭐⭐⭐ |

---

## 核心需求

### 需求层级说明

**P0 (立即启动，关键业务)**: 必须做，3-6个月内完成  
**P1 (高优先级，核心竞争力)**: 应该做，6-12个月内完成  
**P2 (中优先级，生态完善)**: 值得做，12-18个月内完成  
**P3 (低优先级，未来展望)**: 预留方向，长期规划

---

## Phase 1: P0 需求 (第1-3个月：快速验证)

### P0.1 选题与创新性评估模块 (3周)

#### 需求描述

**目标用户**: 硕士、博士研究生（选题阶段）

**核心功能**: 在用户上传初步选题/研究计划时，系统提供：
1. **创新性评估** — 该选题与现有研究的差异
2. **可行性建议** — 技术/资源/时间可行性
3. **相关工作检索** — 自动搜索已有的相关论文
4. **改进建议** — AI给出选题优化方向

#### 功能细节

##### 用户交互流程
```
用户输入：
- 研究方向 (文本，200-500字)
- 拟研究问题 (简洁陈述)
- 学科分类 (下拉选择，对标现有论文类型)
- 学位阶段 (本科/硕士/博士)

系统处理：
① 用 Claude 分析选题核心
② 用 database-lookup 搜索相关文献
③ 生成"创新性评估报告"
④ 对标学校学科评估要求，给出改进建议

输出：
- 选题评分 (1-10分)
  • 创新性: 1-10
  • 可行性: 1-10
  • 重要性: 1-10
- 详细评估报告（Word）
  • 相关工作综述（自动检索的3-5篇论文总结）
  • 创新点分析
  • 技术难点识别
  • 改进建议
- 推荐相关文献（5-10篇）
```

##### 集成的科学代理技能库

- `hypothesis-generation`: 选题建议、创新性分析
- `database-lookup`: 相关文献检索（78个公开数据库）
- `literature-review`: 相关工作自动综述

##### 前端需求

**新增页面**: `/topic-evaluation`

**页面结构**:
```vue
<TopicEvaluation>
  ├── <TopicInputForm>     // 输入选题信息
  ├── <EvaluationProgress> // 处理进度
  └── <ResultView>
      ├── <ScoreCard>      // 三维评分卡
      ├── <RelatedPapers>  // 相关文献列表
      ├── <ImprovementTips>// 改进建议
      └── <DownloadButton> // 下载报告
```

**关键交互**:
- 实时输入检查（字符数、内容合法性）
- 2s 轮询任务状态
- 分阶段展示结果（先显示评分，后补充文献、改进建议）

##### 后端需求

**新增 API 路由**: `/api/v1/topic-evaluation/`

```python
# 新增接口
POST /topic-evaluation/upload
  - 请求: {question, description, discipline, degree_level}
  - 返回: {task_id, status}
  - 配额消耗: 3 credits (比评价稍便宜，鼓励早期使用)

GET /topic-evaluation/status/{task_id}
  - 返回: {status, progress_stage, ...}

GET /topic-evaluation/result/{task_id}
  - 返回: {score, related_papers, improvements, suggestions}

GET /topic-evaluation/download/{task_id}
  - 返回: Word 报告 (含评分表、相关文献、改进建议)
```

**新增 Celery 任务**: `topic_evaluation_tasks.py`

```python
@celery_app.task(queue='evaluation', bind=True)
def run_topic_evaluation(self, task_id, question, description, discipline, degree_level):
    """
    三步流程：
    1. (5%) 解析输入，调用 Claude 分析选题核心
    2. (45%) 用 database_lookup 搜索相关文献（使用 Reactome/KEGG/PubMed 等对应学科的库）
    3. (50%) 生成评估报告和改进建议，导出 Word
    """
    pass
```

**新增核心逻辑**: `app/core/topic_evaluator/`

```
app/core/topic_evaluator/
├── __init__.py
├── prompts.py              # 选题评估的 prompt (按学科分化)
├── evaluator.py            # 核心评估逻辑
├── literature_searcher.py  # 集成 database-lookup
└── report_generator.py     # Word 报告生成
```

**集成现有系统**:
- 配额消耗: `billing_service.consume_quota(user_id, action='topic_evaluation', credits=3)`
- 结果持久化: `TaskRecord` 表新增 `topic_evaluation_results` 字段
- 错误处理: 继承现有的 `ai_client` 双模型容灾

##### 产品定价

| 版本 | 价格 | 包含内容 |
|------|------|--------|
| 免费额度 | 1篇/月 | 基础评分 |
| 单次购买 | 30元/篇 | 完整报告 + 相关文献 |
| 月订阅 | 99元/月 | 无限次评估 + 优先级高 |
| 高校版 | 按机构 | 全校学生可用 + API接入 + 定制学科库 |

##### 时间和人力估算

| 任务 | 时间 | 人力 |
|------|------|------|
| 后端API+Celery任务 | 4天 | 1 senior |
| 前端页面+交互 | 3天 | 1 frontend |
| 提示词优化和测试 | 3天 | 1 PM/AI |
| 数据库调整 | 1天 | 1 DBA |
| QA 和部署 | 2天 | 1 QA |
| **合计** | **3周** | **1-2人** |

---

### P0.2 文献综述初稿生成模块 (2周)

#### 需求描述

**目标用户**: 所有撰写学位论文的学生（文献综述阶段）

**核心功能**: 用户上传已识别的相关论文列表或关键词，系统自动：
1. **检索文献** — 补充用户遗漏的相关论文
2. **分类整理** — 按研究主题/方法/年份分类
3. **生成初稿** — AI写出"文献综述初稿"（500-2000字）
4. **生成Word** — 导出可直接用于论文的初稿

#### 功能细节

##### 用户交互流程

```
输入方式A: 上传论文列表
  文件格式: 
    - 论文题目列表 (txt/csv)
    - BibTeX 格式
    - 手工输入的论文DOI列表

输入方式B: 输入关键词
  关键词: "深度学习 + 图像识别" / "蛋白质折叠"

系统处理：
① (10%) 解析输入，标准化论文信息
② (30%) 用 database-lookup 补充检索相关论文（5-20篇）
③ (30%) 用 Claude 聚类分类（研究方向/方法论/应用领域）
④ (30%) 生成"文献综述初稿"
   - 按分类组织段落
   - 自动插入引文 (APA/GB/T/Vancouver)
   - 生成参考文献表
⑤ 导出 Word (可直接粘入论文)

输出：
- 文献综述初稿（1500-3000字）
  • 研究现状总览
  • 主要研究方向分析
  • 关键问题和挑战
  • 未来研究方向
- 完整的参考文献表（已格式化）
- 论文关键词和分类标签
```

##### 集成的科学代理技能库

- `literature-review`: 自动综述生成的主力
- `database-lookup`: 文献检索和补充
- `citation-management`: 参考文献格式标准化

##### 前端需求

**新增页面**: `/literature-review`

**页面流程**:
```
Step 1: 选择输入方式
  - 上传文件 (txt/csv/bib)
  - 手工输入关键词
  - 粘贴论文标题列表

Step 2: 系统处理
  - 显示识别到的论文数
  - 显示补充检索的新论文
  - 显示分类结果（拓扑图或列表）

Step 3: 查看和编辑
  - 显示生成的初稿
  - 允许编辑（选择/删除某些段落）
  - 预览参考文献格式

Step 4: 下载
  - Word 格式（可直接粘入论文）
  - Markdown 格式
  - 参考文献单独导出
```

##### 后端需求

**新增 API 路由**: `/api/v1/literature-review/`

```python
POST /literature-review/upload
  - 请求: {papers_list: [title/doi], or keywords: str, discipline: str}
  - 返回: {task_id}
  - 配额: 5 credits

GET /literature-review/status/{task_id}
  - 返回: {status, papers_identified, papers_enriched, progress_stage}

GET /literature-review/result/{task_id}
  - 返回: {draft_content, categorization, references, keywords}

GET /literature-review/download/{task_id}
  - 返回: Word 文档
```

**新增 Celery 任务**: `literature_review_tasks.py`

**新增核心逻辑**: `app/core/literature_reviewer/`

```
app/core/literature_reviewer/
├── prompts.py              # 文献综述 prompt
├── paper_parser.py         # 解析用户上传的论文列表
├── enrichment.py           # 集成 database-lookup 补充检索
├── categorizer.py          # 分类组织论文
├── draft_generator.py      # 生成综述初稿
└── report_generator.py     # 导出 Word
```

##### 产品定价

| 版本 | 价格 |
|------|------|
| 单次 | 50元/篇 |
| 月订阅 | 199元/月 (无限次) |

##### 时间估算

| 任务 | 时间 |
|------|------|
| 后端 API + 任务 | 3天 |
| 前端 4 步流程 | 2天 |
| 提示词优化 | 2天 |
| QA | 1天 |
| **合计** | **2周** |

---

### P0.3 增强"期刊投稿指导"功能 (2周)

#### 需求描述

**目标用户**: 准备投稿的研究生

**核心功能**: 在用户完成论文评价后，系统根据评价结果和学科信息，提供：
1. **期刊推荐** — 推荐"与该论文相匹配的期刊" (5-10种)
2. **投稿指南** — 每个期刊的投稿要求、格式、时间
3. **风险评估** — 评估论文被这些期刊接受的概率

#### 功能细节

**集成点**: 在现有的"智能评价"结果页面旁边新增 Tab: "投稿指导"

**流程**:
```
用户完成论文评价 → 看到评价结果 + 评分
→ 点击"投稿指导" Tab
→ 系统推荐 5-10 个相匹配的期刊
→ 每个期刊显示：
   - 影响因子 / JCR 排名
   - 该论文与期刊的契合度评分 (1-10)
   - 投稿要求（论文长度、格式、参考文献格式）
   - 审稿周期
   - 接受率
   - 投稿链接
→ 用户可下载"投稿清单"（包含所有期刊信息）
```

**核心算法**:
```python
def match_journals(evaluation_score, keywords, discipline, paper_type):
    """
    基于：
    1. 论文评价总分（>75 推荐核心期刊）
    2. 关键词匹配
    3. 学科分类
    4. 论文类型（硕士/博士）
    
    返回匹配的期刊列表（按推荐指数排序）
    """
```

##### 集成的科学代理技能库

- `database-lookup`: 期刊信息库查询
- `research-lookup`: 期刊数据检索

##### 前端需求

**在现有页面扩展**: `/evaluation/result/{task_id}`

```vue
<EvaluationResult>
  ├── <Tabs>
  │   ├── <Tab name="评价结果">     // 现有
  │   ├── <Tab name="投稿指导">     // NEW
  │   │   └── <JournalRecommendations>
  │   │       ├── <JournalCard> (重复 5-10 次)
  │   │       │   ├── 期刊名 + JCR排名
  │   │       │   ├── 契合度评分
  │   │       │   ├── 投稿要求摘要
  │   │       │   ├── 审稿周期
  │   │       │   └── "查看详情" 按钮
  │   │       └── <DownloadChecklistBtn>
```

##### 后端需求

**新增 API 路由**:

```python
GET /api/v1/evaluation/journal-recommendations/{task_id}
  - 返回: {journals: [{name, rank, match_score, deadline, ...}]}
  - 无需消耗配额（基于已有的评价结果）

GET /api/v1/evaluation/journal-details/{journal_id}
  - 返回: {name, url, requirements, review_cycle, acceptance_rate, ...}
```

**新增核心逻辑**: `app/core/evaluator/journal_matcher.py`

```python
class JournalMatcher:
    """
    维护期刊元数据（影响因子、分类、投稿链接等）
    实现期刊-论文匹配算法
    """
    
    def get_recommendations(self, evaluation_result, keywords, discipline):
        """基于评价结果推荐期刊"""
        pass
```

##### 期刊数据来源

**建立内部期刊库**:
```
期刊表 (journals):
  - journal_id
  - name (中/英)
  - issn
  - impact_factor (year)
  - jcr_rank
  - jcr_category
  - publisher
  - submission_url
  - typical_review_days
  - acceptance_rate (%)
  - format_requirements (json)
  - is_open_access
```

**数据来源**:
- 中文：高校图书馆期刊库、新华网期刊库、万方期刊库
- 英文：PubMed、Scopus、Web of Science 数据（可用 `database-lookup` 查询）

##### 产品定价

**免费功能**（作为现有评价功能的附加值，无额外收费）

##### 时间估算

| 任务 | 时间 |
|------|------|
| 期刊库建立（脚本导入） | 3天 |
| 匹配算法开发 | 3天 |
| 前端页面 | 2天 |
| QA | 1天 |
| **合计** | **2周** |

---

## Phase 2: P1 需求 (第4-6个月：核心竞争力)

### P1.1 高级写作辅助模块 (3周)

#### 需求描述

**目标用户**: 正在撰写论文初稿的学生

**核心功能**: 
1. **实时语法和风格检查** — 边写边改
2. **学术规范建议** — 学科术语、表述规范
3. **段落逻辑改进** — 逐段落的逻辑连贯性检查
4. **论证强度评估** — 检测论据充分性

#### 技术实现

**集成的科学代理技能库**:
- `scientific-writing`: 高级写作建议
- `scientific-critical-thinking`: 论证逻辑检查

**前端方案**:
```vue
<WritingAssistant>
  ├── <Editor>          // 集成 Monaco/CodeMirror 的富文本编辑器
  ├── <SidePanel>       // 实时反馈面板
  │   ├── <SyntaxIssues>
  │   ├── <LogicChecks>
  │   └── <AcademicStyle>
  └── <SuggestionsPanel> // 段落级建议
```

**交互方式**:
- 用户输入段落 → 2s 后给出实时建议
- 不必等待整篇文章完成，边写边改

##### 时间估算: 3周

---

### P1.2 实验设计评审模块 (2周)

#### 需求描述

**目标用户**: 进行实验研究的学生（理工科）

**核心功能**:
1. **方案审查** — 实验设计的科学性和完整性
2. **风险识别** — 可能的技术/伦理/安全风险
3. **成本预算** — 估算实验所需的成本和时间
4. **方法论建议** — 改进实验设计

#### 技术实现

**集成的科学代理技能库**:
- `experimental-design`: 实验方案评审
- `hypothesis-generation`: 假设验证方法

##### 时间估算: 2周

---

### P1.3 学位论文管理系统（ToB版本 - 高校端）(4周)

#### 需求描述

**目标客户**: 高校教务处、研究生院、学院

**核心功能**:
1. **论文全流程跟踪** — 选题→开题→中期→预答辩→答辩
2. **导师端工具** — 查看学生进度、给出反馈、评阅论文
3. **学院端数据** — 论文质量统计、学位授予数据
4. **数据分析** — 论文完成度、质量趋势、学生满意度

#### 技术实现

**新增模块**: `app/api/v1/institution/`

```python
# 高校机构版本 API
POST /api/v1/institution/create
  - 高校注册（需要校域邮箱验证）

POST /api/v1/institution/students/import
  - 批量导入学生名单（支持教务系统接口）

GET /api/v1/institution/dashboard
  - 全校论文质量统计面板

POST /api/v1/institution/advisor/assign
  - 导师与学生绑定

GET /api/v1/institution/advisor/students
  - 导师查看自己指导的学生列表
```

**定价模型**: 按学校规模年费制
```
小规模（<100学生）: 10万/年
中规模（100-500学生）: 30万/年
大规模（>500学生）: 50万/年
```

##### 时间估算: 4周

---

## Phase 3: P2 需求 (第7-12个月：生态完善)

### P2.1 学术社区功能 (6周)

**概念**: 让学生可以在平台上分享论文、获取同学和教授的反馈

**核心功能**:
1. **论文分享** — 学生可选择性地分享自己的论文初稿
2. **匿名反馈** — 其他学生可以给出评论和建议
3. **教授审阅** — 导师可以在平台上留下批注

**预期价值**: 建立网络效应，提高用户粘性

---

### P2.2 数据分析和可视化增强 (4周)

**新增功能**:
1. **用户论文进度仪表板** — 用户查看自己的多篇论文进度
2. **质量趋势** — 用户写的论文质量是否逐步提升
3. **对标分析** — 与同学科、同学位的论文对比

---

## 实现路线图

### 时间表

```
┌────────────────────────────────────────────────────────────┐
│ 2026年 Q3（第1-3个月）- Phase 1: 快速验证               │
├────────────────────────────────────────────────────────────┤
│ Week 1-3:   P0.1 选题评估模块              (3 weeks)      │
│ Week 3-5:   P0.2 文献综述生成              (2 weeks)      │
│ Week 5-7:   P0.3 期刊投稿指导              (2 weeks)      │
│ Week 7-8:   灰度测试，收集反馈             (1 week)       │
│ Week 8-9:   修复问题，正式发布版本 2.0    (1 week)       │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ 2026年 Q4（第4-6个月）- Phase 2: 核心竞争力             │
├────────────────────────────────────────────────────────────┤
│ Week 10-12: P1.1 高级写作辅助              (3 weeks)      │
│ Week 13-14: P1.2 实验设计评审              (2 weeks)      │
│ Week 14-18: P1.3 学位论文管理系统(ToB)     (4 weeks)      │
│ Week 18-20: 高校试点，销售洽谈             (2 weeks)      │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ 2027年 Q1-Q2（第7-12个月）- Phase 3: 生态完善          │
├────────────────────────────────────────────────────────────┤
│ Week 21-26: P2.1 学术社区功能              (6 weeks)      │
│ Week 27-30: P2.2 数据分析增强              (4 weeks)      │
│ Week 31-32: 整合测试和优化                 (2 weeks)      │
└────────────────────────────────────────────────────────────┘
```

### 里程碑

| 阶段 | 时间 | 目标 | 验收标准 |
|------|------|------|--------|
| **Phase 1 发布** | 2026年9月 | 发布 v2.0（选题+文献+投稿） | 用户数 +50%，留存率 60% |
| **Phase 2 发布** | 2026年12月 | 发布 v2.5（写作+实验+高校版） | 签约5-10所高校 |
| **Phase 3 发布** | 2027年3月 | 发布 v3.0（社区+数据） | 活跃高校20+，月收入 50万+ |

---

## 技术架构

### 系统架构变化

#### 现有架构（v1.0）
```
FastAPI
  ├─ /evaluation    (评价)
  ├─ /proofread     (校对)
  ├─ /formatter     (排版)
  ├─ /plagiarism    (查重)
  ├─ /auth          (认证)
  ├─ /billing       (计费)
  └─ /admin         (管理)

Celery 任务队列
  ├─ evaluation_queue
  ├─ proofread_queue
  ├─ formatter_queue
  └─ plagiarism_queue
```

#### 升级架构（v2.0+）
```
FastAPI
  ├─ /evaluation       (现有，增强)
  ├─ /topic-eval      (NEW) 选题评估
  ├─ /lit-review      (NEW) 文献综述
  ├─ /writing-assist  (NEW) 写作辅助
  ├─ /experiment-eval (NEW) 实验设计
  ├─ /journal-match   (现有评价的扩展)
  ├─ /proofread       (现有)
  ├─ /formatter       (现有)
  ├─ /plagiarism      (现有)
  ├─ /auth            (现有，增强)
  ├─ /billing         (现有，增强)
  ├─ /admin           (现有，增强)
  └─ /institution     (NEW) 高校版本接口

Celery 任务队列 (新增队列)
  ├─ evaluation_queue       (现有)
  ├─ topic_eval_queue      (NEW)
  ├─ lit_review_queue      (NEW)
  ├─ writing_assist_queue  (NEW)
  ├─ experiment_eval_queue (NEW)
  ├─ proofread_queue       (现有)
  ├─ formatter_queue       (现有)
  └─ plagiarism_queue      (现有)

外部服务集成
  ├─ database-lookup     (文献检索、期刊信息)
  ├─ hypothesis-gen      (选题建议)
  ├─ literature-review   (文献综述)
  ├─ experimental-design (实验评审)
  └─ scientific-writing  (写作建议)
```

### 数据库变化

#### 新增表

```sql
-- 选题评估
CREATE TABLE topic_evaluations (
  id INT PRIMARY KEY,
  user_id INT,
  task_id VARCHAR(36),
  question TEXT,
  description TEXT,
  discipline VARCHAR(50),
  degree_level VARCHAR(20),
  evaluation_result JSON,
  related_papers JSON,
  created_at TIMESTAMP
);

-- 文献综述
CREATE TABLE literature_reviews (
  id INT PRIMARY KEY,
  user_id INT,
  task_id VARCHAR(36),
  input_papers JSON,
  enriched_papers JSON,
  categorization JSON,
  draft_content TEXT,
  created_at TIMESTAMP
);

-- 期刊库
CREATE TABLE journals (
  id INT PRIMARY KEY,
  name_zh VARCHAR(200),
  name_en VARCHAR(200),
  issn VARCHAR(20),
  impact_factor FLOAT,
  jcr_rank VARCHAR(50),
  category VARCHAR(100),
  submission_url VARCHAR(500),
  review_days_avg INT,
  acceptance_rate FLOAT,
  format_requirements JSON,
  is_open_access BOOLEAN
);

-- 高校机构
CREATE TABLE institutions (
  id INT PRIMARY KEY,
  name VARCHAR(200),
  domain VARCHAR(100),
  subscription_level VARCHAR(20),
  student_count INT,
  admin_user_ids JSON,
  created_at TIMESTAMP
);

-- 高校学生绑定
CREATE TABLE institution_students (
  institution_id INT,
  user_id INT,
  student_id VARCHAR(50),
  degree_level VARCHAR(20),
  major VARCHAR(100),
  advisor_id INT,
  PRIMARY KEY (institution_id, user_id)
);
```

### 配额体系调整

#### 现有配额模型
```
用途              消耗额度
─────────────────────────
智能评价          5 credits
论文校对          5 credits
模板排版          3 credits
论文查重(中文)    1 credit
论文查重(英文)    2 credits
```

#### 升级后的配额模型
```
用途              消耗额度   说明
──────────────────────────────────────
选题评估          3 credits  鼓励早期使用
文献综述生成      5 credits  
实验设计评审      3 credits  
高级写作辅助      2 credits  每段落
智能评价          5 credits  
论文校对          5 credits  
模板排版          3 credits  
论文查重(中文)    1 credit   
论文查重(英文)    2 credits  
期刊投稿指导      0 credits  免费（基于现有评价）

订阅包
──────────────────────────────────────
学生基础包         99元/月    10 credits/月
学生专业包        199元/月    30 credits/月
学生高级包        399元/月    无限次
高校标准版        50万/年     全校学生无限
高校企业版        100万/年    + 导师端工具 + 数据分析
```

### 与科学代理技能库的集成方式

#### 方式1：直接集成提示词

现有的 `ai_client.py` 已经有了 Claude API 的封装，可以直接补充新的提示词：

```python
# app/core/ai_client.py 新增

PROMPTS = {
    "topic_evaluation": """
    你是一个学位论文选题评审专家...
    [来自 hypothesis-generation 技能的提示词]
    """,
    
    "literature_review": """
    根据以下论文列表，生成一篇文献综述...
    [来自 literature-review 技能的提示词]
    """,
    
    # ... 等等
}
```

#### 方式2：API 调用（未来扩展）

如果 `scientific-agent-skills` 项目有 API 服务化的计划，可以改为：

```python
# 调用远程技能 API
response = requests.post(
    "https://skills-api.example.com/hypothesis-generation",
    json={"topic": "...", "context": "..."}
)
```

#### 方式3：本地技能库（推荐）

将科学代理技能库作为子模块集成到项目中：

```
pdf_check/
├── backend/
│   ├── app/
│   ├── scientific_agent_skills/  (NEW - 添加为 git submodule)
│   │   ├── skills/
│   │   │   ├── hypothesis-generation/
│   │   │   ├── literature-review/
│   │   │   ├── experimental-design/
│   │   │   └── ...
│   │   └── skill_registry.py    (技能索引)
│   └── ...
```

**集成点**:
```python
# app/core/skill_loader.py
from scientific_agent_skills.skill_registry import SkillRegistry

skills = SkillRegistry()
skill = skills.get("hypothesis-generation")
result = skill.execute({"topic": "...", ...})
```

---

## 商业预测

### 收入模型

#### 收入来源

| 来源 | 现状(月) | 6个月后 | 12个月后 | 18个月后 |
|------|---------|--------|---------|---------|
| **ToC - 学生用户** | 4-17万 | 8-25万 | 15-50万 | 25-75万 |
| **ToB - 高校订阅** | 0 | 5-10万 | 25-40万 | 50-100万 |
| **ToB - 企业版** | 0 | 0 | 10万 | 30万 |
| **其他（API、广告）** | 0 | 0-5万 | 5-10万 | 10-20万 |
| **总计** | 4-17万 | 13-40万 | 55-110万 | 115-225万 |

#### 用户增长预测

| 指标 | 现状 | 6个月 | 12个月 | 18个月 |
|------|------|-------|--------|--------|
| **ToC 活跃用户** | 5-10万 | 8-15万 | 15-25万 | 30-50万 |
| **ToC ARPU** | 50-150元 | 100-200元 | 150-300元 | 200-400元 |
| **ToB 签约高校** | 0 | 5-10所 | 20-30所 | 50-80所 |
| **ToB ARPC** | - | 10万/所 | 20万/所 | 30万/所 |

### 定价策略

#### ToC 定价（学生端）

| 功能 | 单次 | 月订阅 | 年订阅 |
|------|------|--------|--------|
| 选题评估 | 30元 | 99元/月 (含其他) | - |
| 文献综述 | 50元 | | |
| 写作辅助 | 按段 2元 | | |
| 智能评价 | 50元 | | |
| 校对 | 50元 | | |
| 排版 | 30元 | | |
| 查重(中文) | 20元 | | |
| 查重(英文) | 50元 | | |
| **组合包** | | | |
| 基础包 | - | 99元/月 | 900元/年 |
| 专业包 | - | 199元/月 | 1800元/年 |
| 高级包 | - | 399元/月 | 3600元/年 |

**基础包内容**: 选题评估 + 文献综述 (各 1 次/月)  
**专业包内容**: + 高级写作 + 实验评审 (各无限)  
**高级包内容**: 所有功能无限使用

#### ToB 定价（高校版）

| 规模 | 价格 | 功能 |
|------|------|------|
| 小规模 (<100学生) | 10万/年 | 基础 4 个功能 + 学生管理 |
| 中规模 (100-500学生) | 30万/年 | 所有学生功能 + 导师端 + 学院数据 |
| 大规模 (>500学生) | 50万/年 | + API 接入 + 定制开发 |

**试点高校优惠**: 前 5 所高校享受 50% 折扣

### 成本结构

#### 一次性成本（开发）

| 项目 | 成本 |
|------|------|
| Phase 1 开发（选题+文献+投稿） | 50万 |
| Phase 2 开发（写作+实验+高校版） | 80万 |
| Phase 3 开发（社区+数据） | 60万 |
| **总计** | **190万** |

#### 月度运营成本

| 项目 | 成本 |
|------|------|
| 服务器（AWS/阿里云） | 5万 |
| Claude API 调用 | 10万 (预计) |
| 外部 API（数据库、期刊库） | 3万 |
| 人员（2-3 开发 + PM） | 50万 |
| 其他（CDN、域名、工具等） | 2万 |
| **月小计** | **70万** |

#### 损益平衡点

```
月收入目标：70万 (=月成本)
单个学生 ARPU: 150元
需要活跃用户数：70万 ÷ 150 = 47万用户

预计时间：
- 现在：5-10万用户，月收入 4-17万
- 6个月后：8-15万用户，月收入 13-40万
- 12个月后：15-25万用户，月收入 55-110万 (已盈亏平衡)
- 18个月后：30-50万用户，月收入 115-225万 (3-5倍利润)

结论：18个月内即可实现完全盈利并收回开发成本
```

---

## 风险与对策

### 技术风险

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| Claude API 价格上涨 | 中 | 中 | 实现本地模型备份（Llama2/Mistral），双模型容灾 |
| 文献库 API 不稳定 | 低 | 中 | 建立本地缓存，降级到公开 API (PubMed/arXiv) |
| 高并发性能问题 | 中 | 中 | 提前做压力测试，增加 Celery 队列隔离 |

### 市场风险

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| 竞争对手快速复制 | 高 | 高 | 快速获得高校合同（ToB锁定），建立学术社区网络效应 |
| 用户接受度不足 | 中 | 中 | Phase 1 灰度测试，收集反馈快速迭代 |
| 高校采购周期长 | 高 | 高 | 先做 ToC 积累数据和案例，用数据打动高校决策者 |
| 学生用户付费意愿低 | 中 | 中 | 提供免费试用（3-5篇），免费版本基础功能 |

### 合规风险

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| 学术诚实性问题（被指控助长抄袭） | 低 | 高 | 清晰的用户协议，强调工具仅用于"辅助写作"，不能直接生成论文 |
| 用户数据隐私 | 中 | 中 | 严格遵守 GDPR/个人信息保护法，论文数据加密存储 |
| 版权问题（文献使用） | 低 | 中 | 仅检索已发表的文献，遵守引用规范，不涉及盗版 |

### 对策总结

**核心防御战略**:
1. **速度** — 快速 Phase 1 上线，抢占市场先发优势
2. **深度** — 通过 Phase 2 高校合作实现 ToB 锁定，建立关系护城河
3. **生态** — 通过 Phase 3 社区功能实现网络效应，建立用户粘性

---

## 附录

### A. 功能优先级矩阵

```
        影响力
        ↑
        │
    P1.3│  ★ Phase 2 (高校版)
        │  / │ (导师端工具)
        │ /  │
    P1.1│★---★ Phase 1 (选题+文献) ★ Phase 3 (社区)
        │ \  │ P0.3 (投稿)
        │  \ │
    P0.1│  ★─────────────────→ 开发成本
        └─────────────────────────
```

**优先级判断标准**:
- 用户需求强度（必须 vs 锦上添花）
- 竞争对手可复制性（易复制 vs 难复制）
- 建立护城河的能力（单点工具 vs 工作流深度）

**结论**: Phase 1 → Phase 2 → Phase 3 是正确的顺序

### B. 与科学代理技能库的技能映射表

| 新功能模块 | 使用的技能库 | 使用方式 |
|----------|----------|--------|
| 选题评估 | hypothesis-generation, database-lookup | 提示词集成 |
| 文献综述 | literature-review, database-lookup, citation-management | 提示词集成 |
| 高级写作 | scientific-writing, scientific-critical-thinking | 提示词集成 |
| 实验评审 | experimental-design, hypothesis-generation | 提示词集成 |
| 期刊投稿 | database-lookup (期刊库) | 数据集成 |
| 学术社区 | peer-review, scholar-evaluation | 提示词集成 |
| 数据分析 | exploratory-data-analysis, statistical-analysis | 后端集成 |

### C. 开发资源需求估算

#### 人力投入

```
Phase 1 (3个月):
  - 1 Senior Backend Engineer
  - 1 Frontend Engineer
  - 1 PM/AI Expert (提示词优化)
  - 0.5 QA

Phase 2 (3个月):
  + 1 Backend Engineer (ToB 系统)
  + 1 Data Engineer (高校数据分析)

Phase 3 (3个月):
  + 1 Full-Stack Engineer (社区功能)
```

#### 预算概算

| 项目 | 成本 |
|------|------|
| 开发人力 (9个月，平均月薪 15万) | 135万 |
| 外包/测试 | 20万 |
| 工具/基础设施升级 | 10万 |
| 市场/销售投入 | 20万 |
| 应急预算 (10%) | 18.5万 |
| **总计** | **203.5万** |

**融资建议**: 寻求 300-500万 融资，用于 18 个月的完整建设 + 运营

### D. 关键 KPI 和追踪

```
用户增长 KPIs:
  - 月新注册用户数 (目标: +50% / 月，Year 1)
  - 活跃用户留存率 (目标: 60%)
  - 每用户平均收入 (ARPU) (目标: 50 → 300元)

商业 KPIs:
  - 月度经常性收入 (MRR) (目标: 4万 → 100万)
  - 客户获取成本 (CAC) (目标: <50元)
  - 用户生命周期价值 (LTV) (目标: >2000元)
  - 高校签约数 (目标: 0 → 50)

产品 KPIs:
  - 新功能采用率 (目标: >30%)
  - 功能使用频次 (目标: 用户月均 >3 次)
  - 功能满意度 (NPS) (目标: >50)

技术 KPIs:
  - 系统可用性 (目标: 99.9%)
  - API 平均响应时间 (目标: <2s)
  - Celery 任务成功率 (目标: >99%)
```

**追踪工具**: 
- Google Analytics (前端)
- 自研 BI 系统 (后端数据)
- Datadog (基础设施监控)

---

## 总结与建议

### 核心结论

1. **现有产品已具有生产级水准和商业模式**，拥有完整的后期论文处理能力

2. **主要缺口在前期功能**（选题→文献→写作），导致用户接触窗口短，防护城河弱

3. **通过集成科学代理技能库中的高价值技能**，可以快速弥补这些缺口

4. **18个月的升级周期是合理的**，分 3 个阶段实施，逐步验证市场

5. **预计 Year 2 可实现 5-10 倍的收入增长和明显的竞争优势**

### 立即行动项

**第 1 周** (这一周):
- [ ] 组织内部评审会议，确认 Phase 1 三个需求的优先级
- [ ] 技术评估：Claude API、database-lookup 集成的具体方案
- [ ] 产品评估：定价策略、用户体验流程
- [ ] 市场评估：竞争对手分析、用户需求验证

**第 2-4 周**:
- [ ] 完成 Phase 1 详细设计文档
- [ ] 启动开发（后端 + 前端并行）
- [ ] 建立 Slack/钉钉 项目通道

**第 5-12 周**:
- [ ] Phase 1 功能开发和灰度测试
- [ ] 与目标高校接触，预热市场

**第 13 周+**:
- [ ] 正式发布 v2.0
- [ ] 推广和用户反馈收集

### 成功衡量

**Phase 1 成功标志**:
- 新功能上线后，用户留存率从 30% 提升至 60%
- 至少 1000 个学生用户尝试新功能
- 正面反馈占比 >70%

**Phase 2 成功标志**:
- 签约 5-10 所高校作为试点
- ToB 收入达到 10万+/月
- 高校对产品的 NPS >50

**Phase 3 成功标志**:
- 50+ 高校订阅
- 用户在平台上分享的论文数 >10万篇
- 平台月活跃用户 >30万

---

**文档编写完成日期**: 2026-06-18  
**下一次审视日期**: 2026-07-15 (启动 Phase 1 后 4 周)

