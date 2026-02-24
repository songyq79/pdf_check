<template>
  <div class="page-container">
    <!-- 欢迎标题 -->
    <div class="welcome-section">
      <h1 class="welcome-title">欢迎使用论文评价检验系统</h1>
      <p class="welcome-description">
        为您的学术论文提供专业的智能评价、错别字检查和格式规范化服务
      </p>
    </div>

    <!-- 功能卡片 -->
    <div class="feature-cards">
      <el-card class="feature-card" shadow="hover" @click="navigateTo('/evaluation')">
        <div class="feature-icon evaluation-icon">
          <el-icon :size="48"><Edit /></el-icon>
        </div>
        <h3 class="feature-title">智能评价</h3>
        <p class="feature-description">
          AI驱动的多维度论文评价，从学术规范性、逻辑创新性、语言质量、文献引用四个维度全面分析
        </p>
        <el-button type="primary" class="feature-button">
          立即使用
        </el-button>
      </el-card>

      <el-card class="feature-card" shadow="hover" @click="navigateTo('/spell-check')">
        <div class="feature-icon spellcheck-icon">
          <el-icon :size="48"><DocumentChecked /></el-icon>
        </div>
        <h3 class="feature-title">错别字检查</h3>
        <p class="feature-description">
          智能检测论文中的错别字、标点符号错误，生成详细的修订报告
        </p>
        <el-button type="success" class="feature-button">
          立即使用
        </el-button>
      </el-card>

      <el-card class="feature-card" shadow="hover" @click="navigateTo('/formatting')">
        <div class="feature-icon formatting-icon">
          <el-icon :size="48"><Document /></el-icon>
        </div>
        <h3 class="feature-title">模板排版</h3>
        <p class="feature-description">
          一键应用标准学术论文模板，自动规范化文档格式、标题、引用等
        </p>
        <el-button type="warning" class="feature-button">
          立即使用
        </el-button>
      </el-card>
    </div>

    <!-- 最近记录 -->
    <div v-if="historyStore.hasRecords" class="recent-section">
      <div class="section-header">
        <h2 class="section-title">
          <el-icon><Clock /></el-icon>
          <span>最近记录</span>
        </h2>
        <el-button type="primary" link @click="navigateTo('/history')">
          查看全部
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>

      <el-card>
        <el-timeline>
          <el-timeline-item
            v-for="record in historyStore.recentRecords"
            :key="record.id"
            :timestamp="formatDate(record.timestamp)"
            placement="top"
          >
            <el-card class="record-card" @click="handleViewRecord(record)">
              <div class="record-header">
                <el-tag :type="getRecordTypeTag(record.type)">
                  {{ getRecordTypeName(record.type) }}
                </el-tag>
                <span class="record-title">{{ getRecordTitle(record) }}</span>
              </div>
              <div v-if="record.type === 'evaluation'" class="record-score">
                综合评分：<span class="score-value">{{ record.result.overall_score }}</span>分
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>

    <!-- 空状态提示 -->
    <div v-else class="empty-state">
      <el-icon class="empty-icon"><FolderOpened /></el-icon>
      <div class="empty-text">暂无历史记录</div>
      <div class="empty-hint">开始使用功能后，记录将显示在这里</div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import {
  Edit,
  DocumentChecked,
  Document,
  Clock,
  ArrowRight,
  FolderOpened
} from '@element-plus/icons-vue'
import { useHistoryStore } from '@/store/modules/history'
import { useEvaluationStore } from '@/store/modules/evaluation'

const router = useRouter()
const historyStore = useHistoryStore()
const evaluationStore = useEvaluationStore()

/**
 * 导航到指定路由
 */
function navigateTo(path) {
  router.push(path)
}

/**
 * 查看记录详情
 */
function handleViewRecord(record) {
  if (record.type === 'evaluation') {
    // 加载记录到评价store
    evaluationStore.currentResult = record.result
    evaluationStore.evaluationStatus = 'completed'
    router.push('/evaluation')
  }
}

/**
 * 获取记录类型标签颜色
 */
function getRecordTypeTag(type) {
  const tagMap = {
    evaluation: 'primary',
    spellcheck: 'success',
    formatting: 'warning'
  }
  return tagMap[type] || 'info'
}

/**
 * 获取记录类型名称
 */
function getRecordTypeName(type) {
  const nameMap = {
    evaluation: '智能评价',
    spellcheck: '错别字检查',
    formatting: '模板排版'
  }
  return nameMap[type] || '未知'
}

/**
 * 获取记录标题
 */
function getRecordTitle(record) {
  if (record.type === 'evaluation') {
    return record.result.paper_title || '未命名论文'
  }
  return record.result.file_name || '未命名文件'
}

/**
 * 格式化日期
 */
function formatDate(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.welcome-section {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  margin-bottom: 30px;
}

.welcome-title {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 15px;
}

.welcome-description {
  font-size: 16px;
  opacity: 0.95;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.feature-card {
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
  padding: 20px;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.evaluation-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.spellcheck-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.formatting-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.feature-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
}

.feature-description {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 20px;
  min-height: 60px;
}

.feature-button {
  width: 100%;
}

.recent-section {
  margin-top: 40px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-card {
  cursor: pointer;
  transition: all 0.3s;
}

.record-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.record-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.record-title {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.record-score {
  font-size: 14px;
  color: #606266;
}

.record-score .score-value {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 80px;
  color: #dcdfe6;
  margin-bottom: 20px;
}

.empty-text {
  font-size: 18px;
  color: #909399;
  margin-bottom: 10px;
}

.empty-hint {
  font-size: 14px;
  color: #c0c4cc;
}
</style>
