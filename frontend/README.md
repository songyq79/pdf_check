# 论文评价检验系统 — 前端说明文档

> **技术栈：** Vue 3 + Pinia + Vue Router 4 + Element Plus  
> **构建工具：** Vite  
> **文档版本：** v1.1（含 Bug Fix）

---

## 目录结构

```
src/
├── api/                        # 后端接口封装
│   ├── index.js                # Axios 实例、拦截器、重试逻辑
│   ├── evaluation.js           # 智能评价接口
│   ├── spellCheck.js           # 错别字检查接口
│   └── formatting.js           # 模板排版接口
│
├── assets/
│   └── styles/
│       ├── global.css          # 全局样式
│       └── responsive.css      # 响应式样式
│
├── components/
│   ├── common/
│   │   ├── FileUpload.vue      # 文件上传组件（拖拽/点击，含空文件校验）
│   │   └── LoadingSpinner.vue  # 加载动画组件
│   ├── charts/
│   │   ├── RadarChart.vue      # 雷达图
│   │   ├── BarChart.vue        # 柱状图
│   │   └── TrendChart.vue      # 趋势图
│   └── evaluation/
│       └── ScoreCard.vue       # 维度评分卡
│
├── router/
│   └── index.js                # 路由配置
│
├── store/
│   └── modules/
│       ├── evaluation.js       # 智能评价状态管理
│       ├── spellCheck.js       # 错别字检查状态管理 ★新增
│       ├── formatting.js       # 模板排版状态管理   ★新增
│       └── history.js          # 历史记录状态管理（localStorage 持久化）
│
├── utils/
│   ├── fileUtils.js            # 文件校验、格式化工具
│   ├── storage.js              # localStorage 封装
│   ├── chartConfig.js          # 图表配置工具
│   └── request.js              # 请求工具（备用）
│
├── views/
│   ├── Home.vue                # 首页
│   ├── Evaluation.vue          # 智能评价页
│   ├── SpellCheck.vue          # 错别字检查页
│   ├── Formatting.vue          # 模板排版页
│   └── History.vue             # 历史记录页
│
└── App.vue                     # 根组件（导航栏 + 路由出口）
```

---

## 路由说明

| 路径 | 页面 | 说明 |
|---|---|---|
| `/` | 首页 | 功能入口 + 最近历史记录 |
| `/evaluation` | 智能评价 | 上传论文，AI 四维度打分 |
| `/spell-check` | 错别字检查 | 上传论文，AI 逐段校对 |
| `/formatting` | 模板排版 | 选模板后上传，自动规范格式 |
| `/history` | 历史记录 | 查看/筛选/删除历史操作 |

---

## 环境变量

在项目根目录创建 `.env.development` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
```

生产环境创建 `.env.production`：

```env
VITE_API_BASE_URL=https://your-api-domain.com
```

---

## 后端接口依赖

后端 Base URL 默认为 `http://localhost:8000`，通过 `VITE_API_BASE_URL` 配置。

### 智能评价

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/evaluation/upload` | 上传文件，返回 `{ task_id }` |
| GET | `/api/v1/evaluation/status/{task_id}` | 轮询状态，返回 `{ status, progress }` |
| GET | `/api/v1/evaluation/result/{task_id}` | 获取完整评价结果 |
| GET | `/api/v1/evaluation/download/{report_id}` | 下载评价报告 |

### 错别字检查

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/proofread/upload` | 上传文件，返回 `{ task_id }` |
| GET | `/api/v1/proofread/status/{task_id}` | 轮询状态，返回 `{ status, progress, stats, finished_at }` |
| GET | `/api/v1/proofread/download/{task_id}` | 下载校对结果文档 |

### 模板排版

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/formatter/templates` | 获取模板列表 |
| POST | `/api/v1/formatter/format` | 提交排版任务，返回 `{ task_id }` |
| GET | `/api/v1/formatter/status/{task_id}` | 轮询状态 |
| GET | `/api/v1/formatter/download/{task_id}` | 下载排版结果文档 |

### 状态轮询返回格式

```json
{
  "status": "processing | completed | failed",
  "progress": 60,
  "error": "错误信息（仅 failed 时）"
}
```

### 评价结果返回格式

```json
{
  "paper_title": "论文标题",
  "overall_score": 85,
  "evaluated_at": "2024-01-01T12:00:00",
  "report_id": "report_xxx",
  "dimensions": {
    "academic": {
      "dimension_name": "学术规范性",
      "score": 88,
      "strengths": ["..."],
      "weaknesses": ["..."],
      "suggestions": ["..."]
    }
  }
}
```

---

## 网络请求规范

| 请求类型 | 超时时间 |
|---|---|
| 文件上传（含 `/upload`、`/format`） | 120 秒 |
| 状态轮询（含 `/status/`、`/health`） | 8 秒 |
| 普通请求 | 30 秒 |

- 5xx 及网络错误自动重试，最多 **2 次**（间隔 1s、2s）
- 4xx 不重试，直接弹出错误提示
- 轮询接口（`/status/`）失败静默处理，不弹窗

---

## 状态管理说明

### evaluationStore

管理智能评价完整流程。

```
idle → uploading → processing → completed
                              ↘ failed
```

| 状态/方法 | 说明 |
|---|---|
| `evaluationStatus` | 当前阶段 |
| `uploadProgress` | 进度值（0-100，只增不减） |
| `currentResult` | 评价结果对象 |
| `uploadAndEvaluate(file)` | 上传并轮询直到完成 |
| `reset()` | 重置为 idle |
| `setPendingResult(result)` | 从历史记录恢复结果 |
| `loadPendingOrReset()` | 页面挂载时调用 |

### spellCheckStore ★新增

管理错别字检查完整流程，状态持久化到 Pinia，切换页面不丢失。

```
idle → processing → completed
                  ↘ failed
```

| 状态/方法 | 说明 |
|---|---|
| `phase` | 当前阶段 |
| `progress` | 进度值（0-100） |
| `stats` | `{ total, changed, skipped }` |
| `uploadAndCheck(file)` | 上传并开始轮询 |
| `cancel()` | 取消任务，重置为 idle |
| `resumeIfProcessing()` | 切回页面时恢复轮询 |
| `stopPolling()` | 暂停轮询（切走页面时调用） |

### formattingStore ★新增

管理模板排版完整流程，状态持久化到 Pinia，切换页面不丢失。

```
idle → processing → completed
                  ↘ failed
```

| 状态/方法 | 说明 |
|---|---|
| `phase` | 当前阶段 |
| `progress` | 进度值（0-100） |
| `selectedTemplateId` | 选中的模板 ID |
| `selectedTemplateName` | 选中的模板名称 |
| `formatResult` | `{ paragraphs, sections, applied, time }` |
| `uploadAndFormat(file, templateId, templateName)` | 上传并开始轮询 |
| `cancel()` | 取消任务，重置为 idle |
| `resumeIfProcessing()` | 切回页面时恢复轮询 |
| `stopPolling()` | 暂停轮询（切走页面时调用） |

### historyStore

历史记录管理，自动持久化到 localStorage（key 前缀：`paper_check_`）。

| 方法 | 说明 |
|---|---|
| `addRecord(record)` | 添加记录 |
| `deleteRecord(id)` | 删除单条 |
| `clearAllRecords()` | 清空全部 |
| `recentRecords` | 最近 5 条（首页展示用） |

---

## 文件上传规范

- **支持格式：** `.docx` 仅此一种
- **大小限制：** ≤ 20MB
- **空文件拦截：** `file.size === 0` 时提示「文件内容为空，请上传有效的文档」
- **重复文件检测：** 同名文件已有历史记录时弹出确认弹窗

---

## Bug 修复记录（v1.0 → v1.1）

| 编号 | 问题描述 | 修复方式 | 涉及文件 |
|---|---|---|---|
| #1 | 左上角标题点击会跳转首页，与导航栏首页重复 | 标题改为 `div`，去掉路由绑定 | `App.vue` |
| #3 | 智能评价进度条上传完成后从 10% 归零 | 进度更新加「只增不减」判断 | `store/modules/evaluation.js` |
| #5 | 评价完成后点导航栏「智能评价」页面无反应 | `router-view` 加 `:key="$route.fullPath"` | `App.vue` |
| #6 | 错别字检查处理中无法中止任务 | 新增「取消校对」按钮 | `views/SpellCheck.vue` |
| #9 | 错别字完成后点导航栏「错别字检查」无反应 | 同 #5，`router-view` key 修复 | `App.vue` |
| #11 | 空文件可以通过校验上传（错别字） | `validateFile` 补充 `size === 0` 判断 | `utils/fileUtils.js` |
| #12 | 模板排版处理中无法中止任务 | 新增「取消排版」按钮 | `views/Formatting.vue` |
| #14 | 空文件可以通过校验上传（模板排版） | 同 #11 | `utils/fileUtils.js` |
| #15 | 排版完成后点导航栏「模板排版」无反应 | 同 #5，`router-view` key 修复 | `App.vue` |
| #17 | 处理中切换页面再切回来，任务中断 | SpellCheck/Formatting 状态提升到 Pinia Store | `store/modules/spellCheck.js`（新增）`store/modules/formatting.js`（新增）`views/SpellCheck.vue` `views/Formatting.vue` |
| #18 | 历史记录点击「筛选」按钮弹出无意义提示 | 移除 `ElMessage.success('筛选成功')`，computed 自动响应 | `views/History.vue` |
| #19 | 历史记录日期筛选当天数据被过滤掉 | `endDate` 加 `86399999ms` 修复至当天末尾 | `views/History.vue` |
| #20 | 首页/历史记录点击错别字、排版记录无反应 | 补充 `spellcheck`、`formatting` 跳转分支 | `views/Home.vue` `views/History.vue` |

---

## 注意事项

**部署前检查清单：**

1. 确认 `VITE_API_BASE_URL` 已正确配置
2. 后端需开启 CORS，允许前端域名跨域请求
3. 后端所有上传接口需支持 `OPTIONS` 预检请求（CORS preflight）
4. `store/modules/spellCheck.js` 和 `store/modules/formatting.js` 为 v1.1 新增文件，升级时注意补充

**开发启动：**

```bash
npm install
npm run dev
```

**生产构建：**

```bash
npm run build
```
