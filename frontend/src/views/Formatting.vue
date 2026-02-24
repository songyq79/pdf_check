<template>
  <div class="page-container">
    <div class="page-title">模板排版</div>
    <div class="page-description">
      选择标准学术论文模板，一键将文档字体、行距、标题层级统一调整为规范格式。
    </div>

    <!-- 选择模板 + 上传（空闲态） -->
    <div v-if="phase === 'idle'">

      <!-- 模板选择 -->
      <el-card class="mb-20">
        <template #header>
          <div class="card-header">
            <el-icon><List /></el-icon>
            <span>选择排版模板</span>
          </div>
        </template>

        <div v-if="templatesLoading" class="loading-tip">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在加载模板列表...
        </div>

        <el-empty v-else-if="templates.length === 0" description="暂无可用模板" />

        <el-radio-group v-else v-model="selectedTemplateId" class="template-group">
          <el-radio
            v-for="t in templates"
            :key="t.id"
            :label="t.id"
            border
            class="template-radio"
          >
            <div class="template-option">
              <div class="template-name">{{ t.name }}</div>
              <div class="template-meta">
                <el-tag size="small" :type="categoryColor(t.category)">
                  {{ categoryLabel(t.category) }}
                </el-tag>
                <span class="template-school">{{ t.school_or_journal }}</span>
              </div>
              <div class="template-desc">{{ t.description }}</div>
            </div>
          </el-radio>
        </el-radio-group>
      </el-card>

      <!-- 文件上传 -->
      <FileUpload
        accept=".docx"
        :max-size="20"
        :disabled="!selectedTemplateId"
        @file-selected="handleFileSelected"
      />
      <div v-if="!selectedTemplateId" class="tip-text">请先选择模板，再上传文件</div>
    </div>

    <!-- 处理中 -->
    <div v-else-if="phase === 'processing'">
      <el-card>
        <LoadingSpinner :size="60" :text="statusText" />
        <div class="mt-20">
          <el-progress :percentage="progress" :stroke-width="10" status="striped" striped-flow />
        </div>
        <div class="file-info mt-10">
          <el-icon><Document /></el-icon>
          <span>{{ currentFilename }}</span>
          <el-divider direction="vertical" />
          <el-icon><Stamp /></el-icon>
          <span>{{ selectedTemplateName }}</span>
        </div>
      </el-card>
    </div>

    <!-- 完成 -->
    <div v-else-if="phase === 'completed'">
      <el-card class="mb-20">
        <el-result
          icon="success"
          title="排版完成"
          :sub-title="`已应用模板：${selectedTemplateName}`"
        >
          <template #extra>
            <div class="result-meta">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="原文件">{{ currentFilename }}</el-descriptions-item>
                <el-descriptions-item label="模板">{{ selectedTemplateName }}</el-descriptions-item>
                <el-descriptions-item label="段落数">{{ formatResult.paragraphs }}</el-descriptions-item>
                <el-descriptions-item label="章节数">{{ formatResult.sections }}</el-descriptions-item>
                <el-descriptions-item label="样式应用">{{ formatResult.applied }} 处</el-descriptions-item>
                <el-descriptions-item label="耗时">{{ formatResult.time }}s</el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
        </el-result>
      </el-card>

      <el-alert
        title="格式化说明"
        type="success"
        :closable="false"
        show-icon
        class="mb-20"
      >
        系统已按所选模板统一调整页面边距、字体、字号、行距及标题层级。下载后直接使用 Word 打开即可。
      </el-alert>

      <div class="button-group">
        <el-button size="large" @click="handleReset">
          <el-icon><RefreshLeft /></el-icon>
          重新排版
        </el-button>
        <el-button type="success" size="large" @click="handleDownload">
          <el-icon><Download /></el-icon>
          下载排版文档
        </el-button>
      </div>
    </div>

    <!-- 失败 -->
    <div v-else-if="phase === 'failed'">
      <el-result icon="error" title="排版失败" :sub-title="errorMsg">
        <template #extra>
          <el-button type="primary" @click="handleReset">重新上传</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import {
  List, Loading, Document, Stamp,
  RefreshLeft, Download,
} from '@element-plus/icons-vue'
import FileUpload from '@/components/common/FileUpload.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import formattingAPI from '@/api/formatting'

// ── 状态 ──────────────────────────────────────────────────
const phase = ref('idle')           // idle | processing | completed | failed
const progress = ref(0)
const currentFilename = ref('')
const currentTaskId = ref(null)
const errorMsg = ref('')

const templates = ref([])
const templatesLoading = ref(true)
const selectedTemplateId = ref('')

const formatResult = ref({
  paragraphs: 0, sections: 0, applied: 0, time: 0,
})

let pollTimer = null

// ── 计算属性 ───────────────────────────────────────────────
const selectedTemplateName = computed(() => {
  const t = templates.value.find(t => t.id === selectedTemplateId.value)
  return t ? t.name : ''
})

const statusText = computed(() => {
  if (progress.value < 20) return '正在上传文件...'
  if (progress.value < 50) return '正在识别文档结构...'
  return '正在应用模板样式，请稍候...'
})

// ── 生命周期 ───────────────────────────────────────────────
onMounted(loadTemplates)
onBeforeUnmount(stopPolling)

// ── 模板加载 ───────────────────────────────────────────────
async function loadTemplates() {
  templatesLoading.value = true
  try {
    const res = await formattingAPI.getTemplates()
    templates.value = (res.templates || []).map(t => ({
      id: t.id,
      name: t.name,
      category: t.category,
      school_or_journal: t.school_or_journal,
      description: t.description,
    }))
    if (templates.value.length > 0) {
      selectedTemplateId.value = templates.value[0].id
    }
  } catch (e) {
    ElMessage.warning('模板列表加载失败，请刷新重试')
  } finally {
    templatesLoading.value = false
  }
}

// ── 文件上传 + 提交格式化 ──────────────────────────────────
async function handleFileSelected(file) {
  if (!selectedTemplateId.value) {
    ElMessage.warning('请先选择模板')
    return
  }
  phase.value = 'processing'
  progress.value = 5
  currentFilename.value = file.name
  errorMsg.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('template_id', selectedTemplateId.value)

    const res = await formattingAPI.format(formData)
    currentTaskId.value = res.task_id
    progress.value = 20

    startPolling(res.task_id)
  } catch (err) {
    phase.value = 'failed'
    errorMsg.value = err?.response?.data?.detail || '提交失败，请重试'
    ElMessage.error(errorMsg.value)
  }
}

// ── 状态轮询 ───────────────────────────────────────────────
function startPolling(taskId) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await formattingAPI.getStatus(taskId)

      if (res.status === 'processing') {
        progress.value = Math.min(85, progress.value + 8)
      } else if (res.status === 'completed') {
        stopPolling()
        const r = res.result || {}
        formatResult.value = {
          paragraphs: r.sections ?? 0,
          sections: r.sections ?? 0,
          applied: r.sections ?? 0,
          time: res.end_time
            ? ((new Date(res.end_time) - new Date(res.start_time)) / 1000).toFixed(1)
            : (r.time_elapsed ?? 0),
        }
        progress.value = 100
        phase.value = 'completed'
        ElMessage.success('排版完成！')
      } else if (res.status === 'failed') {
        stopPolling()
        phase.value = 'failed'
        errorMsg.value = res.error || '排版失败'
        ElMessage.error(errorMsg.value)
      }
    } catch (e) {
      // 网络抖动，继续轮询
    }
  }, 3000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

// ── 下载 ──────────────────────────────────────────────────
function handleDownload() {
  if (!currentTaskId.value) return
  formattingAPI.download(currentTaskId.value)
  ElMessage.success('开始下载排版文档')
}

// ── 重置 ──────────────────────────────────────────────────
function handleReset() {
  stopPolling()
  phase.value = 'idle'
  progress.value = 0
  currentFilename.value = ''
  currentTaskId.value = null
  formatResult.value = { paragraphs: 0, sections: 0, applied: 0, time: 0 }
}

// ── 辅助 ──────────────────────────────────────────────────
function categoryLabel(cat) {
  return { universities: '高校', journals: '期刊', custom: '自定义' }[cat] ?? cat
}
function categoryColor(cat) {
  return { universities: 'primary', journals: 'success', custom: 'info' }[cat] ?? ''
}
</script>

<style scoped>
.template-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}
.template-radio {
  width: 100%;
  height: auto;
  padding: 14px 16px;
  margin-right: 0 !important;
}
.template-option { text-align: left; }
.template-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}
.template-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.template-school { font-size: 12px; color: #606266; }
.template-desc { font-size: 12px; color: #909399; line-height: 1.5; }

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
}
.loading-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  padding: 20px 0;
}
.tip-text {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}
.file-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 13px;
}
.result-meta { width: 100%; margin-top: 16px; }
.button-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.mt-10 { margin-top: 10px; }
.mt-20 { margin-top: 20px; }
.mb-20 { margin-bottom: 20px; }
</style>
