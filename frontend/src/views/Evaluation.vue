<template>
  <div class="page-container">
    <div class="page-title">智能评价</div>
    <div class="page-description">
      上传您的学术论文（.docx格式），系统将从学术规范性、逻辑与创新性、语言质量、文献引用规范性四个维度进行智能评价。
    </div>

    <!-- IDLE状态：文件上传 -->
    <div v-if="evaluationStore.isIdle">
      <FileUpload
        accept=".docx"
        :max-size="20"
        @file-selected="handleFileSelected"
      />
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
          <div style="margin-top:8px; font-size:12px; color:#909399;">
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
        <div style="font-size: 18px; font-weight: bold; color: #303133; display:flex; align-items:center; gap:8px;">
          <el-icon><Reading /></el-icon>
          {{ evaluationStore.currentResult.paper_title }}
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: #909399;">
          评价时间：{{ formatDate(evaluationStore.currentResult.evaluated_at) }}
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
        <el-button type="primary" size="large" @click="evaluationStore.reset()">
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
  // 加载待展示结果或保持当前状态
  evaluationStore.loadPendingOrKeep()
  evaluationStore.resumeIfProcessing()
  
  // 移除自动重置逻辑，用户需要主动点击"重新评价"按钮才会重置
  // 这样刷新页面、切换菜单后都能保持结果显示
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
  if (p < 30) return '#909399'
  if (p < 70) return '#409eff'
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

// 评分等级
const scoreLevel = computed(() => {
  const score = evaluationStore.currentResult?.overall_score || 0
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '中等'
  if (score >= 60) return '及格'
  return '需要改进'
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
    ElMessage.success('评价完成！')
  } catch (error) {
    ElMessage.error(error.message || '评价失败，请重试')
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
.score-subtitle {
  font-size: 18px;
  opacity: 0.9;
}
</style>
