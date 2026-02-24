<template>
  <div class="page-container">
    <div class="page-title">错别字检查</div>
    <div class="page-description">
      上传您的学术论文（.docx格式），AI 将逐段校对错别字与标点，输出带 Word 修订标记的文档供您审阅接受。
    </div>

    <!-- 上传区域 -->
    <div v-if="phase === 'idle'">
      <FileUpload
        accept=".docx"
        :max-size="20"
        @file-selected="handleFileSelected"
      />
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
        </div>
      </el-card>
    </div>

    <!-- 完成结果 -->
    <div v-else-if="phase === 'completed'">
      <!-- 统计概览 -->
      <el-card class="mb-20">
        <div class="result-summary">
          <div class="summary-item">
            <div class="summary-icon total-icon">
              <el-icon :size="36"><Document /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">总段落数</div>
              <div class="summary-value">{{ stats.total }}</div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-icon changed-icon">
              <el-icon :size="36"><WarningFilled /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">发现并修改</div>
              <div class="summary-value text-danger">{{ stats.changed }}</div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-icon ok-icon">
              <el-icon :size="36"><CircleCheckFilled /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">无需修改</div>
              <div class="summary-value text-success">{{ stats.skipped }}</div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-icon time-icon">
              <el-icon :size="36"><Clock /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">完成时间</div>
              <div class="summary-value small">{{ formatDate(finishedAt) }}</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 说明 -->
      <el-alert
        title="校对结果说明"
        type="success"
        :closable="false"
        show-icon
        class="mb-20"
      >
        <template #default>
          AI 已将修订建议以 <strong>Word 修订模式</strong>写入文档。
          下载后使用 Word 打开，可逐条 <em>接受/拒绝</em> 每处修改。
        </template>
      </el-alert>

      <!-- 操作按钮 -->
      <div class="button-group">
        <el-button size="large" @click="handleReset">
          <el-icon><RefreshLeft /></el-icon>
          <span>重新检查</span>
        </el-button>
        <el-button type="success" size="large" @click="handleDownload">
          <el-icon><Download /></el-icon>
          <span>下载校对文档</span>
        </el-button>
      </div>
    </div>

    <!-- 失败 -->
    <div v-else-if="phase === 'failed'">
      <el-result icon="error" title="校对失败" :sub-title="errorMsg">
        <template #extra>
          <el-button type="primary" @click="handleReset">重新上传</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import {
  WarningFilled, CircleCheckFilled,
  Document, Clock, RefreshLeft, Download,
} from '@element-plus/icons-vue'
import FileUpload from '@/components/common/FileUpload.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import spellCheckAPI from '@/api/spellCheck'

const phase = ref('idle')        // idle | processing | completed | failed
const progress = ref(0)
const currentFilename = ref('')
const currentTaskId = ref(null)
const stats = ref({ total: 0, changed: 0, skipped: 0 })
const finishedAt = ref(null)
const errorMsg = ref('')

let pollTimer = null

const statusText = computed(() => {
  if (progress.value < 10) return '正在上传文件...'
  if (progress.value < 50) return '正在初始化校对任务...'
  return 'AI 逐段校对中，请稍候（视文档长度约需 1-3 分钟）...'
})

/**
 * 文件选中后上传并启动轮询
 */
async function handleFileSelected(file) {
  phase.value = 'processing'
  progress.value = 5
  currentFilename.value = file.name
  errorMsg.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await spellCheckAPI.upload(formData)
    currentTaskId.value = res.task_id
    progress.value = 15

    // 开始轮询状态
    startPolling(res.task_id)
  } catch (err) {
    phase.value = 'failed'
    errorMsg.value = err?.response?.data?.detail || '上传失败，请重试'
    ElMessage.error(errorMsg.value)
  }
}

function startPolling(taskId) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await spellCheckAPI.getStatus(taskId)

      if (res.status === 'processing') {
        progress.value = Math.min(90, progress.value + 5)
      } else if (res.status === 'completed') {
        stopPolling()
        stats.value = res.stats || { total: 0, changed: 0, skipped: 0 }
        finishedAt.value = res.finished_at
        progress.value = 100
        phase.value = 'completed'
        ElMessage.success('校对完成！')
      } else if (res.status === 'failed') {
        stopPolling()
        phase.value = 'failed'
        errorMsg.value = res.error || '校对失败'
        ElMessage.error(errorMsg.value)
      }
    } catch (e) {
      // 网络抖动，继续轮询
    }
  }, 3000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onBeforeUnmount(stopPolling)

function handleReset() {
  stopPolling()
  phase.value = 'idle'
  progress.value = 0
  currentFilename.value = ''
  currentTaskId.value = null
  stats.value = { total: 0, changed: 0, skipped: 0 }
  finishedAt.value = null
}

function handleDownload() {
  if (!currentTaskId.value) return
  spellCheckAPI.download(currentTaskId.value)
  ElMessage.success('开始下载校对文档')
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<style scoped>
.result-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
}
.summary-item {
  display: flex;
  align-items: center;
  gap: 14px;
}
.summary-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}
.total-icon   { background: linear-gradient(135deg,#4facfe,#00f2fe); }
.changed-icon { background: linear-gradient(135deg,#f093fb,#f5576c); }
.ok-icon      { background: linear-gradient(135deg,#43e97b,#38f9d7); }
.time-icon    { background: linear-gradient(135deg,#fa8231,#f9ca24); }
.summary-label { font-size: 13px; color: #909399; margin-bottom: 4px; }
.summary-value { font-size: 28px; font-weight: bold; color: #303133; }
.summary-value.small { font-size: 13px; font-weight: normal; }
.text-danger  { color: #f56c6c; }
.text-success { color: #67c23a; }
.file-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 13px;
}
.button-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.mt-10 { margin-top: 10px; }
.mt-20 { margin-top: 20px; }
.mb-20 { margin-bottom: 20px; }
</style>
