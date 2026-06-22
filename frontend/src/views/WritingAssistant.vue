<template>
  <div class="page-container">
    <div class="page-title">高级写作辅助</div>
    <div class="page-description">
      AI 从语法、风格、逻辑、论证四个维度给出具体修改建议（只诊断、不代写，最终修改由你决定）。
    </div>

    <!-- 模式 Tab -->
    <div class="wa-tabs">
      <button class="wa-tab" :class="{ active: mode === 'single' }" @click="mode = 'single'">单段速查</button>
      <button class="wa-tab" :class="{ active: mode === 'whole' }" @click="mode = 'whole'">整篇检查</button>
    </div>

    <!-- ===== 单段速查 ===== -->
    <div v-if="mode === 'single'" class="wa-layout">
      <el-card class="wa-editor">
        <div class="wa-toolbar">
          <el-radio-group v-model="paperType" size="small">
            <el-radio-button value="humanities">人文社科</el-radio-button>
            <el-radio-button value="science_engineering">理工农医</el-radio-button>
            <el-radio-button value="arts">艺术</el-radio-button>
          </el-radio-group>
          <span class="wa-count">{{ paragraph.length }} 字</span>
        </div>
        <el-input v-model="paragraph" type="textarea" :rows="16" maxlength="2000"
          placeholder="粘贴或输入要检查的论文段落（单段，≤2000 字）..." />
        <div class="wa-submit">
          <CostHint action="writing_assist" />
          <el-button type="primary" :loading="loading" :disabled="!paragraph.trim()" @click="handleCheck">
            检查本段
          </el-button>
        </div>
      </el-card>

      <el-card class="wa-panel">
        <div v-if="!result" class="wa-empty">
          <el-icon :size="40" color="#cbd5e1"><EditPen /></el-icon>
          <p>填写段落后点「检查本段」，这里显示四维建议</p>
        </div>
        <div v-else>
          <div class="wa-overall" v-if="result.overall">
            <strong>总评：</strong> {{ result.overall }}
            <span class="wa-issuecount">共 {{ result.issue_count }} 处建议</span>
          </div>
          <div v-if="result.issue_count === 0" class="wa-clean">✅ 未发现明显问题，写得不错！</div>
          <div v-for="dim in dims" :key="dim.key" v-show="result[dim.key]?.length">
            <div class="wa-dim-title" :style="{ color: dim.color }">{{ dim.label }}（{{ result[dim.key].length }}）</div>
            <div v-for="(item, i) in result[dim.key]" :key="i" class="wa-item">
              <div class="wa-excerpt">「{{ item.excerpt }}」</div>
              <div class="wa-issue">⚠ {{ item.issue }}</div>
              <div class="wa-suggestion">💡 {{ item.suggestion }}</div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- ===== 整篇检查 ===== -->
    <div v-else>
      <!-- 上传 -->
      <el-card v-if="!wholeResult && !wholeRunning" class="wa-upload-card">
        <div class="wa-toolbar">
          <el-radio-group v-model="paperType" size="small">
            <el-radio-button value="humanities">人文社科</el-radio-button>
            <el-radio-button value="science_engineering">理工农医</el-radio-button>
            <el-radio-button value="arts">艺术</el-radio-button>
          </el-radio-group>
        </div>
        <FileUpload accept=".docx" :max-size="20" @file-selected="onFileSelected" />
        <div class="upload-tip">仅支持 .docx；自动跳过图片、表格、标题，逐段给四维建议（图表内容不检查）。</div>
        <div style="text-align:center; margin-top:14px;">
          <CostHint action="writing_whole" />
        </div>
        <div style="text-align:center; margin-top:14px;">
          <el-button type="primary" size="large" :loading="wholeSubmitting" :disabled="!wholeFile" @click="handleCheckDocument">
            开始整篇检查
          </el-button>
          <div v-if="wholeFile" class="wa-filename">已选择：{{ wholeFile.name }}</div>
        </div>
      </el-card>

      <!-- 进度 -->
      <el-card v-else-if="wholeRunning" style="text-align:center; padding:32px;">
        <el-progress type="circle" :percentage="wholeProgress" :color="'#006C49'" />
        <div style="margin-top:16px; color:#374151;">{{ wholeMessage || '正在逐段分析…' }}</div>
        <div style="margin-top:6px; font-size:12px; color:#9ca3af;">整篇分析需要一些时间，请勿关闭页面</div>
      </el-card>

      <!-- 结果 -->
      <div v-else>
        <el-card class="wa-summary">
          <div class="sum-row">
            <div class="sum-item"><div class="sum-num">{{ wholeResult.total_paragraphs }}</div><div class="sum-label">文档总段</div></div>
            <div class="sum-item"><div class="sum-num">{{ wholeResult.checked }}</div><div class="sum-label">已送检段</div></div>
            <div class="sum-item"><div class="sum-num">{{ wholeResult.paragraphs.length }}</div><div class="sum-label">有建议段</div></div>
            <div class="sum-item"><div class="sum-num">{{ wholeResult.total_issues }}</div><div class="sum-label">建议总数</div></div>
            <div class="sum-act">
              <el-button @click="resetWhole">重新检查</el-button>
            </div>
          </div>
          <!-- 维度筛选 -->
          <div class="dim-filter">
            <button class="dim-chip" :class="{ active: dimFilter === 'all' }" @click="dimFilter = 'all'">全部</button>
            <button v-for="d in dims" :key="d.key" class="dim-chip" :class="{ active: dimFilter === d.key }"
              :style="dimFilter === d.key ? { color: '#fff', background: d.color, borderColor: d.color } : { color: d.color }"
              @click="dimFilter = d.key">
              {{ d.label }}
            </button>
          </div>
        </el-card>

        <div v-if="wholeResult.paragraphs.length === 0" class="wa-clean" style="text-align:center; padding:40px;">
          ✅ 全文未发现明显问题，写得不错！
        </div>

        <el-card v-for="p in filteredParagraphs" :key="p.index" class="wa-para-card">
          <div class="para-head">
            <span class="para-idx">第 {{ p.index + 1 }} 段</span>
            <span class="para-issuecount">{{ p.issue_count }} 处建议</span>
          </div>
          <div class="para-text">{{ p.text }}</div>
          <div v-for="dim in visibleDims" :key="dim.key" v-show="p[dim.key]?.length">
            <div class="wa-dim-title" :style="{ color: dim.color }">{{ dim.label }}（{{ p[dim.key].length }}）</div>
            <div v-for="(item, i) in p[dim.key]" :key="i" class="wa-item">
              <div class="wa-excerpt">「{{ item.excerpt }}」</div>
              <div class="wa-issue">⚠ {{ item.issue }}</div>
              <div class="wa-suggestion">💡 {{ item.suggestion }}</div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { EditPen } from '@element-plus/icons-vue'
import writingAPI from '@/api/writingAssistant'
import CostHint from '@/components/common/CostHint.vue'
import FileUpload from '@/components/common/FileUpload.vue'

const mode = ref('single')
const paperType = ref('humanities')

const dims = [
  { key: 'grammar', label: '语法', color: '#dc2626' },
  { key: 'style', label: '风格', color: '#d97706' },
  { key: 'logic', label: '逻辑', color: '#2563eb' },
  { key: 'argument', label: '论证', color: '#7c3aed' },
]

// ── 单段 ──
const paragraph = ref('')
const loading = ref(false)
const result = ref(null)

async function handleCheck() {
  if (!paragraph.value.trim()) return
  loading.value = true
  try {
    result.value = await writingAPI.check(paragraph.value, paperType.value)
  } catch (e) { /* 拦截器处理 */ } finally {
    loading.value = false
  }
}

// ── 整篇 ──
const wholeFile = ref(null)
const wholeSubmitting = ref(false)
const wholeRunning = ref(false)
const wholeProgress = ref(0)
const wholeMessage = ref('')
const wholeResult = ref(null)
const dimFilter = ref('all')
let pollTimer = null

function onFileSelected(file) { wholeFile.value = file }

const visibleDims = computed(() => dimFilter.value === 'all' ? dims : dims.filter(d => d.key === dimFilter.value))
const filteredParagraphs = computed(() => {
  if (!wholeResult.value) return []
  if (dimFilter.value === 'all') return wholeResult.value.paragraphs
  return wholeResult.value.paragraphs.filter(p => (p[dimFilter.value] || []).length > 0)
})

async function handleCheckDocument() {
  if (!wholeFile.value) return
  wholeSubmitting.value = true
  try {
    const res = await writingAPI.checkDocument(wholeFile.value, paperType.value)
    wholeSubmitting.value = false
    wholeRunning.value = true
    wholeProgress.value = 0
    pollStatus(res.task_id)
  } catch (e) {
    wholeSubmitting.value = false
    // 402/错误由拦截器处理
  }
}

function pollStatus(taskId) {
  if (pollTimer) clearInterval(pollTimer)
  let attempts = 0
  pollTimer = setInterval(async () => {
    attempts++
    try {
      const s = await writingAPI.documentStatus(taskId)
      wholeProgress.value = s.progress || 0
      wholeMessage.value = s.message || ''
      if (s.status === 'completed') {
        clearInterval(pollTimer); pollTimer = null
        const r = await writingAPI.documentResult(taskId)
        wholeResult.value = r
        wholeRunning.value = false
        ElMessage.success('整篇检查完成')
      } else if (s.status === 'failed') {
        clearInterval(pollTimer); pollTimer = null
        wholeRunning.value = false
        ElMessage.error('检查失败：' + (s.error || '请重试'))
      }
    } catch (e) { /* 轮询错误忽略 */ }
    if (attempts > 300) { clearInterval(pollTimer); pollTimer = null; wholeRunning.value = false; ElMessage.warning('检查超时，请稍后查看') }
  }, 2000)
}

function resetWhole() {
  wholeResult.value = null
  wholeFile.value = null
  wholeProgress.value = 0
  dimFilter.value = 'all'
}

onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<style scoped>
.wa-tabs { display: inline-flex; gap: 4px; background: #f3f4f6; border-radius: 12px; padding: 4px; margin-bottom: 20px; }
.wa-tab { border: none; background: transparent; padding: 8px 22px; border-radius: 9px; font-size: 14px; color: rgb(107,114,128); cursor: pointer; font-weight: 500; }
.wa-tab.active { background: #fff; color: #006C49; font-weight: 600; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }

.wa-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 900px) { .wa-layout { grid-template-columns: 1fr; } }
.wa-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.wa-count { font-size: 12px; color: rgb(156,163,175); }
.wa-submit { display: flex; align-items: center; justify-content: flex-end; gap: 16px; margin-top: 12px; }

.wa-panel { min-height: 400px; }
.wa-empty { text-align: center; color: rgb(156,163,175); padding: 80px 20px; }
.wa-empty p { margin-top: 12px; font-size: 13px; }
.wa-overall { font-size: 14px; color: rgb(31,41,55); background: rgba(0,108,73,0.05); border-radius: 12px; padding: 12px; margin-bottom: 16px; }
.wa-issuecount { float: right; font-size: 12px; color: #006C49; }
.wa-clean { font-size: 14px; color: #008000; padding: 12px 0; }
.wa-dim-title { font-size: 14px; font-weight: 600; margin: 14px 0 8px; }
.wa-item { border-left: 3px solid #e5e7eb; padding: 6px 0 6px 12px; margin-bottom: 10px; }
.wa-excerpt { font-size: 13px; color: rgb(75,85,99); font-style: italic; margin-bottom: 4px; }
.wa-issue { font-size: 13px; color: #b45309; margin-bottom: 2px; }
.wa-suggestion { font-size: 13px; color: rgb(31,41,55); }

.upload-tip { text-align: center; font-size: 12px; color: rgb(156,163,175); margin-top: 12px; }
.wa-filename { font-size: 12px; color: #006C49; margin-top: 8px; }

.wa-summary { margin-bottom: 16px; }
.sum-row { display: flex; align-items: center; gap: 28px; }
.sum-item { text-align: center; }
.sum-num { font-family: 'Newsreader', serif; font-size: 30px; font-weight: 600; color: #006C49; line-height: 1; }
.sum-label { font-size: 12px; color: rgb(107,114,128); margin-top: 4px; }
.sum-act { margin-left: auto; }
.dim-filter { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; }
.dim-chip { border: 1px solid #e5e7eb; background: #fff; border-radius: 100px; padding: 4px 14px; font-size: 13px; cursor: pointer; color: rgb(107,114,128); }
.dim-chip.active { background: #006C49; color: #fff; border-color: #006C49; }

.wa-para-card { margin-bottom: 14px; }
.para-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.para-idx { font-size: 13px; font-weight: 700; color: #1f2937; }
.para-issuecount { font-size: 12px; color: #006C49; }
.para-text { font-size: 13px; color: rgb(75,85,99); background: #f9fafb; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; line-height: 1.6; }

:deep(.el-card) { border-radius: 20px; border: 1px solid rgba(229,231,235,0.5); box-shadow: 0 4px 32px rgba(0,0,0,0.06); }
:deep(.el-button--primary) { background: rgb(0,108,73); border-color: rgb(0,108,73); border-radius: 9999px; }
:deep(.el-button--primary:hover) { background: rgb(0,90,60); border-color: rgb(0,90,60); }
:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: rgba(79,251,182,0.08); border-color: rgb(0,108,73) !important;
  color: rgb(0,108,73); box-shadow: -1px 0 0 0 rgb(0,108,73);
}
</style>
