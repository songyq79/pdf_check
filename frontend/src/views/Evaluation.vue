<template>
  <div class="page-container">
    <div class="page-title">智能评价</div>
    <div class="page-description">
      上传您的学术论文（.docx格式），系统将从学术规范性、逻辑与创新性、语言质量、文献引用规范性四个维度进行智能评价。
    </div>

    <!-- IDLE状态：显示文件上传组件 -->
    <div v-if="evaluationStore.isIdle">
      <FileUpload
        accept=".docx"
        :max-size="20"
        @file-selected="handleFileSelected"
      />
    </div>

    <!-- UPLOADING/PROCESSING状态：显示加载状态 -->
    <div v-else-if="evaluationStore.isUploading || evaluationStore.isProcessing">
      <el-card>
        <LoadingSpinner
          :size="60"
          :text="loadingText"
        />
        <div v-if="evaluationStore.isUploading" class="mt-20">
          <el-progress
            :percentage="evaluationStore.uploadProgress"
            :stroke-width="10"
            :color="progressColor"
          />
        </div>
      </el-card>
    </div>

    <!-- COMPLETED状态：显示评价结果 -->
    <div v-else-if="evaluationStore.isCompleted && evaluationStore.currentResult">
      <!-- 综合评分 -->
      <div class="score-display">
        <div class="score-label">综合评分</div>
        <div class="score-value">{{ evaluationStore.currentResult.overall_score }}</div>
        <div class="score-subtitle">{{ scoreLevel }}</div>
      </div>

      <!-- 论文标题 -->
      <el-card class="mb-20">
        <div style="font-size: 18px; font-weight: bold; color: #303133;">
          <el-icon><Reading /></el-icon>
          {{ evaluationStore.currentResult.paper_title }}
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: #909399;">
          评价时间：{{ formatDate(evaluationStore.currentResult.evaluated_at) }}
        </div>
      </el-card>

      <!-- 雷达图 -->
      <el-card class="mb-20">
        <RadarChart :dimension-scores="dimensionScores" />
      </el-card>

      <!-- 柱状图 -->
      <el-card class="mb-20">
        <BarChart :dimension-scores="dimensionScores" />
      </el-card>

      <!-- 各维度详细评分 -->
      <div class="card-container" style="grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));">
        <ScoreCard
          v-for="(dimension, key) in evaluationStore.currentResult.dimensions"
          :key="key"
          :dimension-name="key"
          :score="dimension.score"
          :strengths="dimension.strengths"
          :weaknesses="dimension.weaknesses"
          :suggestions="dimension.suggestions"
        />
      </div>

      <!-- 操作按钮 -->
      <div class="button-group mt-20">
        <el-button type="primary" size="large" @click="handleReset">
          <el-icon><RefreshLeft /></el-icon>
          <span>重新评价</span>
        </el-button>
        <el-button type="success" size="large" @click="handleDownloadReport">
          <el-icon><Download /></el-icon>
          <span>下载报告</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Reading, RefreshLeft, Download } from '@element-plus/icons-vue'
import { useEvaluationStore } from '@/store/modules/evaluation'
import FileUpload from '@/components/common/FileUpload.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import RadarChart from '@/components/charts/RadarChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import ScoreCard from '@/components/evaluation/ScoreCard.vue'
import evaluationAPI from '@/api/evaluation'

const evaluationStore = useEvaluationStore()

// 加载文字
const loadingText = computed(() => {
  if (evaluationStore.isUploading) {
    return '正在上传文件...'
  } else if (evaluationStore.isProcessing) {
    return '正在分析论文，请稍候...'
  }
  return ''
})

// 进度条颜色
const progressColor = computed(() => {
  const progress = evaluationStore.uploadProgress
  if (progress < 30) return '#909399'
  if (progress < 70) return '#409eff'
  return '#67c23a'
})

// 维度分数对象（用于图表）
const dimensionScores = computed(() => {
  if (!evaluationStore.currentResult?.dimensions) return {}
  const scores = {}
  Object.keys(evaluationStore.currentResult.dimensions).forEach(key => {
    scores[key] = evaluationStore.currentResult.dimensions[key].score
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

/**
 * 处理文件选择
 */
async function handleFileSelected(file) {
  try {
    await evaluationStore.uploadAndEvaluate(file)
    ElMessage.success('评价完成！')
  } catch (error) {
    console.error('评价失败:', error)
    ElMessage.error(error.message || '评价失败，请重试')
  }
}

/**
 * 重置状态，重新评价
 */
function handleReset() {
  evaluationStore.reset()
}

/**
 * 下载报告
 */
function handleDownloadReport() {
  const reportId = evaluationStore.currentResult?.report_id
  if (!reportId) {
    ElMessage.warning('报告未生成，请稍后重试')
    return
  }
  evaluationAPI.downloadReport(reportId)
  ElMessage.success('开始下载评价报告')
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
/* 页面特定样式已在全局样式中定义 */
</style>
