<template>
  <div class="page-container">
    <div class="page-title">智能评价</div>
    <div class="page-description">
      上传您的学术论文（支持 .docx / .pdf），系统将依据山东省本科毕业论文抽检评议标准，从选题意义、写作安排、逻辑构建、专业能力、学术规范五个维度进行智能评价。
    </div>

    <!-- IDLE状态：论文类别选择 + 文件上传 -->
    <div v-if="evaluationStore.isIdle">
      <!-- 论文类别选择 -->
      <el-card class="mb-20 paper-type-card">
        <div class="paper-type-title">请选择论文类别</div>
        <div class="paper-type-subtitle">不同类别的论文将使用对应的评议要素标准进行评价</div>
        <el-radio-group v-model="evaluationStore.paperType" class="paper-type-group">
          <el-radio-button value="humanities">
            <div class="radio-label">
              <div class="radio-title">人文社科类（第Ⅰ类）</div>
              <div class="radio-desc">哲学、经济学、法学、教育学、文学、历史学、管理学</div>
            </div>
          </el-radio-button>
          <el-radio-button value="science_engineering">
            <div class="radio-label">
              <div class="radio-title">理工农医类（第Ⅱ类）</div>
              <div class="radio-desc">理学、工学、农学、医学、建筑学</div>
            </div>
          </el-radio-button>
          <el-radio-button value="arts">
            <div class="radio-label">
              <div class="radio-title">艺术类（第Ⅲ类）</div>
              <div class="radio-desc">艺术学</div>
            </div>
          </el-radio-button>
        </el-radio-group>
      </el-card>

      <FileUpload
        accept=".docx,.pdf"
        :max-size="20"
        @file-selected="handleFileSelected"
      />
      <div class="upload-tip">
        支持 .docx 和 .pdf(文字版),扫描版 PDF 无法解析
      </div>
    </div>

    <!-- UPLOADING/PROCESSING状态：加载中 -->
    <div v-else-if="evaluationStore.isUploading || evaluationStore.isProcessing">
      <el-card style="text-align:center; padding: 20px;">
        <LoadingSpinner
          :size="60"
          :text="loadingText"
        />
        <div class="mt-20" style="max-width:400px; margin: 0 auto;">
          <el-progress
            :percentage="evaluationStore.uploadProgress"
            :stroke-width="10"
            :color="progressColor"
            :status="evaluationStore.uploadProgress >= 100 ? 'success' : undefined"
          />
          <div style="margin-top:8px; font-size:12px; color:rgb(107,114,128);">
            {{ evaluationStore.isUploading ? '正在上传文件...' : '正在进行多维度分析（可能需要1-3分钟）...' }}
          </div>
        </div>
        <div class="mt-20">
          <el-button @click="handleCancel">
            <el-icon><CircleClose /></el-icon>
            <span>取消评价</span>
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- FAILED状态 -->
    <div v-else-if="evaluationStore.isFailed">
      <el-card>
        <el-result
          icon="error"
          title="评价失败"
          :sub-title="evaluationStore.error || '请检查网络连接或API配置后重试'"
        >
          <template #extra>
            <el-button type="primary" @click="evaluationStore.reset()">重新上传</el-button>
          </template>
        </el-result>
      </el-card>
    </div>

    <!-- COMPLETED状态：显示结果 -->
    <div v-else-if="evaluationStore.isCompleted && evaluationStore.currentResult">
      <!-- 降级模式警告 -->
      <el-alert
        v-if="evaluationStore.warning"
        type="warning"
        :title="evaluationStore.warning"
        :closable="false"
        show-icon
        class="mb-20"
      >
        <template #default>
          <div style="font-size: 13px; line-height: 1.6;">
            系统已自动从文档中提取文本内容进行评价，但可能丢失了部分格式信息。
            <br>
            建议：在 Word 中打开文档，选择"另存为"，保存为新的 .docx 文件后重新上传。
          </div>
        </template>
      </el-alert>
      
      <!-- 综合评分 -->
      <div class="score-display mb-20">
        <div class="score-label">综合评分</div>
        <div class="score-value">{{ evaluationStore.currentResult.overall_score }}</div>
        <div class="score-subtitle" style="font-size:18px; opacity:0.9;">{{ scoreLevel }}</div>
      </div>

      <!-- 论文标题 -->
      <el-card class="mb-20">
        <div style="font-size: 18px; font-weight: bold; color: rgb(18,18,18); display:flex; align-items:center; gap:8px;">
          <el-icon><Reading /></el-icon>
          {{ evaluationStore.currentResult.paper_title }}
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: rgb(107,114,128); display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
          <span>评价时间：{{ formatDate(evaluationStore.currentResult.evaluated_at) }}</span>
          <el-tag v-if="evaluationStore.currentResult.paper_type_name" size="small" type="info">
            {{ evaluationStore.currentResult.paper_type_name }}
          </el-tag>
        </div>
      </el-card>

      <!-- 图表区域 -->
      <div class="card-container mb-20" style="grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));">
        <el-card>
          <RadarChart :dimension-scores="dimensionScores" />
        </el-card>
        <el-card>
          <BarChart :dimension-scores="dimensionScores" />
        </el-card>
      </div>

      <!-- 各维度详细评分 -->
      <div class="card-container mb-20" style="grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));">
        <ScoreCard
          v-for="(dimension, key) in evaluationStore.currentResult.dimensions"
          :key="key"
          :dimension-name="dimension.dimension_name || key"
          :score="dimension.score"
          :strengths="dimension.strengths"
          :weaknesses="dimension.weaknesses"
          :suggestions="dimension.suggestions"
        />
      </div>

      <!-- 操作按钮 -->
      <div class="button-group">
        <el-button type="primary" size="large" @click="handleReset">
          <el-icon><RefreshLeft /></el-icon>
          <span>重新评价</span>
        </el-button>
        <el-button
          type="success"
          size="large"
          :disabled="!evaluationStore.currentResult.report_id"
          @click="handleDownloadReport"
        >
          <el-icon><Download /></el-icon>
          <span>下载报告</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Reading, RefreshLeft, Download, CircleClose } from '@element-plus/icons-vue'
import { useEvaluationStore } from '@/store/modules/evaluation'
import { useHistoryStore } from '@/store/modules/history'
import { useRoute } from 'vue-router'
import FileUpload from '@/components/common/FileUpload.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import RadarChart from '@/components/charts/RadarChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import ScoreCard from '@/components/evaluation/ScoreCard.vue'
import evaluationAPI from '@/api/evaluation'

const evaluationStore = useEvaluationStore()
const historyStore = useHistoryStore()
const route = useRoute()

onMounted(() => {
  console.log('[Evaluation] onMounted 开始')
  console.log('[Evaluation] pendingResult:', evaluationStore.pendingResult)
  console.log('[Evaluation] isCompleted:', evaluationStore.isCompleted)
  console.log('[Evaluation] currentResult:', evaluationStore.currentResult)
  
  // 检查是否从历史记录页面跳转过来
  const fromHistory = route.query.from === 'history'
  console.log('[Evaluation] fromHistory:', fromHistory)
  
  // 如果从历史记录来的，尝试加载 pendingResult（会检查 sessionStorage）
  if (fromHistory) {
    console.log('[Evaluation] 从历史记录来的，调用 loadPendingOrKeep')
    evaluationStore.loadPendingOrKeep()
  }
  // 如果没有 pendingResult，但是状态是 completed，且不是从历史记录来的，需要重置
  else if (evaluationStore.isCompleted && !fromHistory) {
    console.log('[Evaluation] 状态是 completed 且不是从历史记录来的，调用 reset')
    evaluationStore.reset()
  }
  else {
    console.log('[Evaluation] 保持当前状态')
  }
  // 其他情况（idle、processing、failed 或从历史记录刷新）保持当前状态
  
  // 如果正在处理中，恢复轮询
  evaluationStore.resumeIfProcessing()
})

onBeforeUnmount(() => evaluationStore.stopPolling())

// 监听路由变化，当从其他页面返回时恢复状态
watch(() => route.path, (newPath) => {
  if (newPath === '/evaluation') {
    if (evaluationStore.isProcessing) {
      // 如果正在处理，恢复轮询
      evaluationStore.resumeIfProcessing()
    }
  }
})

// 加载提示文字
const loadingText = computed(() => {
  if (evaluationStore.isUploading) return '正在上传文件...'
  if (evaluationStore.isProcessing) return '正在分析论文，请稍候...'
  return ''
})

// 进度条颜色
const progressColor = computed(() => {
  const p = evaluationStore.uploadProgress
  if (p < 30) return 'rgb(107,114,128)'
  if (p < 70) return '#006C49'
  return '#67c23a'
})

// 维度分数（使用中文名作key以匹配雷达图配置）
const dimensionScores = computed(() => {
  const dims = evaluationStore.currentResult?.dimensions
  if (!dims) return {}
  const scores = {}
  Object.values(dims).forEach(dim => {
    const name = dim.dimension_name || ''
    if (name) scores[name] = dim.score
  })
  return scores
})

// 评分等级（四档制，依据山东省标准）
const scoreLevel = computed(() => {
  const score = evaluationStore.currentResult?.overall_score || 0
  if (score >= 90) return '优秀'
  if (score >= 75) return '良好'
  if (score >= 60) return '合格'
  return '不合格'
})

async function handleFileSelected(file) {
  const duplicate = historyStore.records.find(
    r => r.type === 'evaluation' && r.result?.file_name === file.name
  )
  if (duplicate) {
    try {
      await ElMessageBox.confirm(
        `"${file.name}" 已有评价记录，重复上传将重新生成报告，是否继续？`,
        '重复文档',
        { confirmButtonText: '继续评价', cancelButtonText: '取消', type: 'warning' }
      )
    } catch {
      return
    }
  }
  try {
    await evaluationStore.uploadAndEvaluate(file)
  } catch (error) {
    if (error.response?.status !== 402) {
      ElMessage.error(error.message || '评价失败，请重试')
    }
  }
}

function handleDownloadReport() {
  const reportId = evaluationStore.currentResult?.report_id
  if (!reportId) {
    ElMessage.warning('报告未生成，请稍后重试')
    return
  }
  evaluationAPI.downloadReport(reportId)
  ElMessage.success('开始下载评价报告')
}

function handleCancel() {
  evaluationStore.cancel()
  ElMessage.info('已取消评价')
}

function handleReset() {
  evaluationStore.reset()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}
</script>

<style scoped>
.upload-tip {
  margin-top: 12px;
  font-size: 13px;
  color: rgb(107, 114, 128);
  text-align: center;
}

.score-subtitle {
  font-size: 18px;
  opacity: 0.9;
}

.paper-type-card {
  text-align: center;
}

.paper-type-title {
  font-size: 16px;
  font-weight: 500;
  color: rgb(18, 18, 18);
  margin-bottom: 6px;
}

.paper-type-subtitle {
  font-size: 13px;
  color: rgb(107, 114, 128);
  margin-bottom: 20px;
}

.paper-type-group {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.paper-type-group .el-radio-button {
  flex: 1;
  min-width: 200px;
  max-width: 280px;
}

.paper-type-group :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 16px 12px;
  white-space: normal;
  height: auto;
  line-height: 1.5;
  border-radius: 16px !important;
  border: 1px solid rgba(229, 231, 235, 0.50) !important;
  box-shadow: none !important;
}

.paper-type-group :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: rgba(79, 251, 182, 0.08);
  border-color: rgb(0, 108, 73) !important;
  color: rgb(18, 18, 18);
}

.radio-label {
  text-align: center;
}

.radio-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}

.radio-desc {
  font-size: 12px;
  color: rgb(107, 114, 128);
  line-height: 1.4;
}

.paper-type-group :deep(.is-active) .radio-desc {
  color: rgb(0, 108, 73);
}

:deep(.el-card) {
  border-radius: 24px;
  border: 1px solid rgba(229, 231, 235, 0.50);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
}

:deep(.el-button--primary) {
  background: rgb(0, 108, 73);
  border-color: rgb(0, 108, 73);
  border-radius: 9999px;
}

:deep(.el-button--primary:hover) {
  background: rgb(0, 90, 60);
  border-color: rgb(0, 90, 60);
}

:deep(.el-progress-bar__inner) {
  background: rgb(0, 108, 73);
}
</style>
