<template>
  <div class="modern-page-container">
    <!-- 欢迎区域 -->
    <section class="modern-welcome-section">
      <h1 class="modern-welcome-title">欢迎使用<br>论文评价检验系统</h1>
      <p class="modern-welcome-subtitle">为您的学术论文提供专业的质量检测与智能评价</p>
      <p class="modern-welcome-description">
        请拉起袖子准备迎战吧！错别字、语法、段落逻辑，统统交给我们。
        无需烦恼，只需上传文档，坐等专业反馈与自动修正。
      </p>
    </section>

    <!-- 功能卡片 -->
    <div class="modern-features-grid">
      <div class="modern-feature-card" @click="navigateTo('/evaluation')">
        <div class="modern-feature-icon icon-gradient-blue">
          <el-icon :size="36"><Edit /></el-icon>
        </div>
        <h3 class="modern-feature-title">智能评价</h3>
        <p class="modern-feature-description">
          从四个维度进行全面评价：从学术规范性、逻辑与创新性、语言质量、文献引用规范性等多个角度，提供详细的评价报告和改进建议。
        </p>
        <el-button type="primary" class="modern-feature-button" size="large">立即使用</el-button>
      </div>

      <div class="modern-feature-card" @click="navigateTo('/spell-check')">
        <div class="modern-feature-icon icon-gradient-red">
          <el-icon :size="36"><DocumentChecked /></el-icon>
        </div>
        <h3 class="modern-feature-title">错别字检查</h3>
        <p class="modern-feature-description">
          利用先进的 AI 技术，对论文进行逐段校对，标记并修正文字错误、语法问题、标点符号使用不当等问题，确保文字表达准确无误。
        </p>
        <el-button type="success" class="modern-feature-button" size="large">立即使用</el-button>
      </div>

      <div class="modern-feature-card" @click="navigateTo('/formatting')">
        <div class="modern-feature-icon icon-gradient-cyan">
          <el-icon :size="36"><Document /></el-icon>
        </div>
        <h3 class="modern-feature-title">模板排版</h3>
        <p class="modern-feature-description">
          提供多种学术论文模板（如清华、北大、IEEE、APA 等格式），自动识别文档结构，一键应用专业排版样式，让您的论文符合投稿要求。
        </p>
        <el-button type="warning" class="modern-feature-button" size="large">立即使用</el-button>
      </div>
    </div>

    <!-- 数据统计 -->
    <section class="modern-stats-section">
      <div class="modern-stats-grid">
        <div class="modern-stat-item">
          <div class="modern-stat-value">98.5%</div>
          <div class="modern-stat-label">准确率</div>
        </div>
        <div class="modern-stat-item">
          <div class="modern-stat-value">500+</div>
          <div class="modern-stat-label">服务用户</div>
        </div>
        <div class="modern-stat-item">
          <div class="modern-stat-value">200万+</div>
          <div class="modern-stat-label">处理字数</div>
        </div>
        <div class="modern-stat-item">
          <div class="modern-stat-value">24/7</div>
          <div class="modern-stat-label">在线服务</div>
        </div>
      </div>
    </section>

    <!-- 最近记录 -->
    <section v-if="historyStore.hasRecords" class="modern-history-section">
      <div class="modern-section-header">
        <h2 class="modern-section-title">
          <el-icon><Clock /></el-icon>
          <span style="margin-left: 8px;">最近记录</span>
        </h2>
        <el-button type="primary" link @click="navigateTo('/history')">
          查看全部
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>

      <el-table :data="historyStore.recentRecords" style="width: 100%">
        <el-table-column label="文件名" min-width="200">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span>📄</span>
              <span>{{ getRecordTitle(row) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getRecordTypeTag(row.type)">
              {{ getRecordTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default>
            <el-tag type="success">已完成</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewRecord(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 空状态提示 -->
    <section v-else class="modern-history-section">
      <div class="empty-state">
        <el-icon class="empty-icon" :size="80"><FolderOpened /></el-icon>
        <div class="empty-text">暂无历史记录</div>
        <div class="empty-hint">开始使用功能后，记录将显示在这里</div>
      </div>
    </section>
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
import { useSpellCheckStore } from '@/store/modules/spellCheck'
import { useFormattingStore } from '@/store/modules/formatting'

const router = useRouter()
const historyStore = useHistoryStore()
const evaluationStore = useEvaluationStore()
const spellCheckStore = useSpellCheckStore()
const formattingStore = useFormattingStore()

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
    evaluationStore.setPendingResult(record.result)
    router.push('/evaluation')
  } else if (record.type === 'spellcheck') {
    spellCheckStore.setPendingResult(record.result)
    router.push('/spell-check')
  } else if (record.type === 'formatting') {
    formattingStore.setPendingResult(record.result)
    router.push('/formatting')
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
/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
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

/* 响应式优化 */
@media (max-width: 1024px) {
  .modern-features-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .modern-welcome-section {
    padding: 40px 15px;
  }

  .modern-welcome-title {
    font-size: 32px;
  }

  .modern-welcome-subtitle {
    font-size: 18px;
  }

  .modern-stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }

  .modern-stat-value {
    font-size: 32px;
  }
}

@media (max-width: 480px) {
  .modern-feature-card {
    padding: 24px;
  }

  .modern-feature-icon {
    width: 64px;
    height: 64px;
  }

  .modern-feature-title {
    font-size: 18px;
  }

  .modern-feature-description {
    font-size: 13px;
    min-height: auto;
  }
}
</style>
