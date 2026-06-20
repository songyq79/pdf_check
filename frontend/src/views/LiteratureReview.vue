<template>
  <div class="page-container">
    <div class="page-title">文献综述生成</div>
    <div class="page-description">
      上传论文列表（txt/csv/bib）或填写关键词，AI 自动补检文献、按主题聚类，生成可二次编辑的文献综述初稿与 GB/T 7714 参考文献（消耗 5 次额度）。
    </div>

    <!-- 表单 -->
    <div v-if="state === 'form'">
      <el-card class="mb-20">
        <el-tabs v-model="inputMode">
          <el-tab-pane label="上传论文列表" name="file">
            <el-upload
              drag
              :auto-upload="false"
              :limit="1"
              accept=".txt,.csv,.bib"
              :on-change="onFileChange"
              :on-remove="() => (form.file = null)"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">拖拽文件到此，或<em>点击上传</em></div>
              <template #tip>
                <div class="upload-tip">支持 .txt（每行一个标题）/ .csv（title,authors,year）/ .bib（BibTeX）</div>
              </template>
            </el-upload>
          </el-tab-pane>
          <el-tab-pane label="输入关键词" name="keywords">
            <el-input
              v-model="form.keywords"
              type="textarea"
              :rows="3"
              placeholder="多个关键词用逗号分隔，如：深度学习, 图像识别, 语义分割"
            />
          </el-tab-pane>
        </el-tabs>

        <el-divider />

        <el-form :model="form" label-position="top">
          <div class="form-row">
            <el-form-item label="综述主题" class="form-col">
              <el-input v-model="form.topic" placeholder="如：深度学习在医学影像中的应用（选填）" />
            </el-form-item>
            <el-form-item label="学科" class="form-col">
              <el-input v-model="form.discipline" placeholder="如：计算机科学" />
            </el-form-item>
          </div>
          <el-form-item label="论文类别">
            <el-radio-group v-model="form.paper_type" class="type-group">
              <el-radio-button value="humanities">人文社科类</el-radio-button>
              <el-radio-button value="science_engineering">理工农医类</el-radio-button>
              <el-radio-button value="arts">艺术类</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-form>

        <div class="submit-bar">
          <span class="cost-hint">本次生成消耗 <strong>5</strong> 次额度</span>
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
            生成综述初稿
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 处理 -->
    <div v-else-if="state === 'processing'">
      <el-card style="text-align:center; padding:40px 20px;">
        <el-icon class="spin" :size="48" color="#006C49"><Loading /></el-icon>
        <div style="margin:16px 0 8px; font-size:16px; font-weight:600;">{{ progressMsg }}</div>
        <div style="max-width:420px; margin:16px auto 0;">
          <el-progress :percentage="progress" :stroke-width="10" color="#006C49" />
        </div>
        <div class="mt-20"><el-button @click="handleReset">取消</el-button></div>
      </el-card>
    </div>

    <!-- 失败 -->
    <div v-else-if="state === 'failed'">
      <el-card>
        <el-result icon="error" title="生成失败" :sub-title="errorMsg || '请稍后重试'">
          <template #extra><el-button type="primary" @click="handleReset">重新填写</el-button></template>
        </el-result>
      </el-card>
    </div>

    <!-- 结果 -->
    <div v-else-if="state === 'result' && result">
      <el-alert
        type="info" :closable="false" show-icon class="mb-20"
        title="本综述为 AI 生成初稿，请务必二次修改完善后再使用（学术诚信要求）"
      />

      <el-card class="mb-20">
        <div class="meta-row">
          <el-tag type="success" effect="plain">共 {{ result.meta.papers_total }} 篇文献</el-tag>
          <el-tag v-if="result.meta.discipline" type="info" effect="plain">{{ result.meta.discipline }}</el-tag>
          <span class="meta-topic">{{ result.meta.topic || '文献综述初稿' }}</span>
        </div>
      </el-card>

      <!-- 总览 -->
      <el-card v-if="result.draft.overview" class="mb-20">
        <div class="block-title">研究现状总览</div>
        <p class="prose">{{ result.draft.overview }}</p>
      </el-card>

      <!-- 各小节 -->
      <el-card v-for="(sec, i) in result.draft.sections" :key="i" class="mb-20">
        <div class="block-title">{{ i + 1 }}. {{ sec.title }}</div>
        <p class="prose">{{ sec.content }}</p>
      </el-card>

      <!-- 研究空白 -->
      <el-card v-if="(result.categorization.research_gaps || []).length" class="mb-20">
        <div class="block-title">🔍 研究空白与未来方向</div>
        <ul><li v-for="(g,i) in result.categorization.research_gaps" :key="i">{{ g }}</li></ul>
      </el-card>

      <!-- 结论 -->
      <el-card v-if="result.draft.conclusion" class="mb-20">
        <div class="block-title">结论</div>
        <p class="prose">{{ result.draft.conclusion }}</p>
      </el-card>

      <!-- 参考文献 -->
      <el-card class="mb-20">
        <div class="block-title">参考文献（{{ result.papers.length }}，GB/T 7714）</div>
        <div v-for="(p,i) in result.papers" :key="i" class="paper-item">
          <span class="paper-idx">[{{ i + 1 }}]</span>
          <span>{{ (p.authors || []).slice(0,3).join(', ') }}. {{ p.title }}. {{ p.year || '—' }}</span>
        </div>
      </el-card>

      <div class="button-group">
        <el-button size="large" @click="handleReset">
          <el-icon><RefreshLeft /></el-icon><span>重新生成</span>
        </el-button>
        <el-button type="success" size="large" :disabled="!result.report_id" @click="handleDownload">
          <el-icon><Download /></el-icon><span>下载 Word</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, RefreshLeft, Download, UploadFilled } from '@element-plus/icons-vue'
import litAPI from '@/api/literatureReview'

const state = ref('form')
const inputMode = ref('file')
const submitting = ref(false)
const progress = ref(0)
const progressMsg = ref('正在生成...')
const errorMsg = ref('')
const result = ref(null)

let pollTimer = null
let taskId = null

const form = ref({
  file: null,
  keywords: '',
  topic: '',
  discipline: '',
  paper_type: 'humanities',
  citation_style: 'gbt7714',
})

function onFileChange(uploadFile) {
  form.value.file = uploadFile.raw
}

async function handleSubmit() {
  const hasFile = inputMode.value === 'file' && form.value.file
  const hasKw = inputMode.value === 'keywords' && form.value.keywords.trim()
  if (!hasFile && !hasKw) {
    ElMessage.warning('请上传论文列表文件，或填写关键词')
    return
  }
  // 仅提交当前输入方式的数据
  const payload = { ...form.value }
  if (inputMode.value === 'file') payload.keywords = ''
  else payload.file = null

  submitting.value = true
  try {
    const res = await litAPI.submit(payload)
    taskId = res.task_id
    state.value = 'processing'
    progress.value = 10
    progressMsg.value = '任务已提交，正在解析文献...'
    startPolling()
  } catch (e) {
    // 402/错误由全局拦截器处理
  } finally {
    submitting.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const s = await litAPI.getStatus(taskId)
      if (typeof s.progress === 'number') progress.value = s.progress
      if (s.progress_stage) progressMsg.value = s.progress_stage
      if (s.status === 'completed') {
        stopPolling()
        await fetchResult()
      } else if (s.status === 'failed') {
        stopPolling()
        errorMsg.value = s.error || '生成失败'
        state.value = 'failed'
      }
    } catch (e) { /* 轮询静默 */ }
  }, 2000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function fetchResult() {
  try {
    result.value = await litAPI.getResult(taskId)
    state.value = 'result'
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    errorMsg.value = e._userMessage || '获取结果失败'
    state.value = 'failed'
  }
}

function handleDownload() {
  if (!result.value?.report_id) { ElMessage.warning('报告未生成'); return }
  litAPI.downloadReport(result.value.report_id)
  ElMessage.success('开始下载综述报告')
}

function handleReset() {
  stopPolling()
  taskId = null
  result.value = null
  progress.value = 0
  errorMsg.value = ''
  state.value = 'form'
}

onBeforeUnmount(stopPolling)
</script>

<style scoped>
.form-row { display: flex; gap: 16px; }
.form-col { flex: 1; }
.type-group { display: flex; gap: 8px; flex-wrap: wrap; }
.submit-bar { display: flex; align-items: center; justify-content: flex-end; gap: 16px; margin-top: 8px; }
.cost-hint { font-size: 13px; color: rgb(107,114,128); }
.cost-hint strong { color: #006C49; }
.upload-tip { font-size: 12px; color: rgb(156,163,175); margin-top: 6px; }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.meta-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.meta-topic { font-size: 16px; font-weight: 600; color: rgb(31,41,55); }

.block-title { font-size: 16px; font-weight: 600; margin-bottom: 12px; color: rgb(17,24,39); }
.prose { font-size: 14px; line-height: 1.9; color: rgb(55,65,81); white-space: pre-wrap; margin: 0; }
ul { padding-left: 20px; margin: 0; }
ul li { font-size: 14px; line-height: 1.8; color: rgb(55,65,81); }

.paper-item { padding: 7px 0; border-bottom: 1px solid rgba(0,0,0,.05); font-size: 13px; color: rgb(55,65,81); }
.paper-idx { color: #006C49; font-weight: 600; margin-right: 6px; }

.button-group { display: flex; gap: 12px; justify-content: center; }

:deep(.el-card) {
  border-radius: 24px;
  border: 1px solid rgba(229, 231, 235, 0.50);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
}
:deep(.el-button--primary) {
  background: rgb(0, 108, 73); border-color: rgb(0, 108, 73); border-radius: 9999px;
}
:deep(.el-button--primary:hover) { background: rgb(0, 90, 60); border-color: rgb(0, 90, 60); }
:deep(.el-tabs__item.is-active) { color: #006C49; }
:deep(.el-tabs__active-bar) { background: #006C49; }
:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: rgba(79, 251, 182, 0.08);
  border-color: rgb(0, 108, 73) !important;
  color: rgb(0, 108, 73);
  box-shadow: -1px 0 0 0 rgb(0,108,73);
}
</style>
