<template>
  <div class="page-container">
    <div class="page-title">错别字检查</div>
    <div class="page-description">
      上传您的学术论文（.docx格式），AI 将逐段校对错别字与标点，输出带 Word 修订标记的文档供您审阅接受。
    </div>

    <!-- 上传区域 -->
    <div v-if="store.isIdle">
      <FileUpload
        accept=".docx"
        :max-size="20"
        @file-selected="handleFileSelected"
      />
    </div>

    <!-- 处理中 -->
    <div v-else-if="store.isProcessing">
      <el-card>
        <LoadingSpinner :size="60" :text="store.statusText" />
        <div class="mt-20">
          <el-progress :percentage="store.progress" :stroke-width="10" status="striped" striped-flow />
        </div>
        <div class="file-info mt-10">
          <el-icon><Document /></el-icon>
          <span>{{ store.currentFilename }}</span>
        </div>
        <div class="mt-20" style="text-align:center;">
          <el-button @click="handleCancel">
            <el-icon><CircleClose /></el-icon>
            <span>取消校对</span>
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 完成结果 -->
    <div v-else-if="store.isCompleted">
      <!-- 降级模式警告 -->
      <el-alert
        v-if="store.warning"
        type="warning"
        :title="store.warning"
        :closable="false"
        show-icon
        class="mb-20"
      >
        <template #default>
          <div style="font-size: 13px; line-height: 1.6;">
            系统已自动从文档中提取文本内容进行校对，但可能丢失了部分格式信息。
            <br>
            建议：在 Word 中打开文档，选择"另存为"，保存为新的 .docx 文件后重新上传。
          </div>
        </template>
      </el-alert>
      
      <el-card class="mb-20">
        <div class="result-summary">
          <div class="summary-item">
            <div class="summary-icon total-icon">
              <el-icon :size="36"><Document /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">总段落数</div>
              <div class="summary-value">{{ store.stats.total }}</div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-icon changed-icon">
              <el-icon :size="36"><WarningFilled /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">发现并修改</div>
              <div class="summary-value text-danger">{{ store.stats.changed }}</div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-icon ok-icon">
              <el-icon :size="36"><CircleCheckFilled /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">无需修改</div>
              <div class="summary-value text-success">{{ store.stats.skipped }}</div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-icon time-icon">
              <el-icon :size="36"><Clock /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">完成时间</div>
              <div class="summary-value small">{{ formatDate(store.finishedAt) }}</div>
            </div>
          </div>
        </div>
      </el-card>

      <el-alert title="校对结果说明" type="success" :closable="false" show-icon class="mb-20">
        <template #default>
          AI 已将修订建议以 <strong>Word 修订模式</strong>写入文档。
          下载后使用 Word 打开，可逐条 <em>接受/拒绝</em> 每处修改。
        </template>
      </el-alert>

      <div class="button-group">
        <el-button size="large" @click="store.reset()">
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
    <div v-else-if="store.isFailed">
      <el-result icon="error" title="校对失败" :sub-title="store.errorMsg">
        <template #extra>
          <el-button type="primary" @click="store.reset()">重新上传</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import {
  WarningFilled, CircleCheckFilled,
  Document, Clock, RefreshLeft, Download, CircleClose,
} from '@element-plus/icons-vue'
import FileUpload from '@/components/common/FileUpload.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import spellCheckAPI from '@/api/spellCheck'
import { useSpellCheckStore } from '@/store/modules/spellCheck'
import { useHistoryStore } from '@/store/modules/history'

const store = useSpellCheckStore()
const historyStore = useHistoryStore()
const route = useRoute()

// 加载待展示结果或保持当前状态
onMounted(() => {
  store.loadPendingOrKeep()
  store.resumeIfProcessing()
  
  // 移除自动重置逻辑，用户需要主动点击"重新检查"按钮才会重置
  // 这样刷新页面、切换菜单后都能保持结果显示
})
onBeforeUnmount(() => store.stopPolling())

// 监听路由变化，当从其他页面返回时恢复状态
watch(() => route.path, (newPath) => {
  if (newPath === '/spell-check') {
    // 如果是处理中状态，恢复轮询
    if (store.isProcessing) {
      store.resumeIfProcessing()
    }
  }
})

async function handleFileSelected(file) {
  const duplicate = historyStore.records.find(
    r => r.type === 'spellcheck' && r.result?.file_name === file.name
  )
  if (duplicate) {
    try {
      await ElMessageBox.confirm(
        `"${file.name}" 已有校对记录，重复上传将重新生成文档，是否继续？`,
        '重复文档',
        { confirmButtonText: '继续校对', cancelButtonText: '取消', type: 'warning' }
      )
    } catch {
      return
    }
  }
  await store.uploadAndCheck(file)
  if (store.isFailed) {
    ElMessage.error(store.errorMsg || '上传失败，请重试')
  }
}

function handleCancel() {
  store.cancel()
  ElMessage.info('已取消校对')
}

function handleDownload() {
  if (!store.currentTaskId) return
  spellCheckAPI.download(store.currentTaskId)
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
.summary-item { display: flex; align-items: center; gap: 14px; }
.summary-icon {
  width: 56px; height: 56px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: white; flex-shrink: 0;
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
.file-info { display: flex; align-items: center; gap: 6px; color: #909399; font-size: 13px; }
.button-group { display: flex; gap: 12px; flex-wrap: wrap; }
.mt-10 { margin-top: 10px; }
.mt-20 { margin-top: 20px; }
.mb-20 { margin-bottom: 20px; }
</style>
