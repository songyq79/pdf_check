<template>
  <div class="page-container">
    <div class="page-title">历史记录</div>
    <div class="page-description">
      查看所有评价、检查和排版的历史记录
    </div>

    <!-- 筛选器 -->
    <el-card class="mb-20">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="类型">
          <el-select v-model="filterForm.type" placeholder="全部类型" clearable style="width: 150px;">
            <el-option label="全部类型" value="" />
            <el-option label="智能评价" value="evaluation" />
            <el-option label="错别字检查" value="spellcheck" />
            <el-option label="模板排版" value="formatting" />
            <el-option label="论文查重" value="plagiarism" />
          </el-select>
        </el-form-item>

        <el-form-item label="查重语种" v-if="filterForm.type === '' || filterForm.type === 'plagiarism'">
          <el-select v-model="filterForm.engineLang" placeholder="全部" clearable style="width: 120px;">
            <el-option label="全部" value="" />
            <el-option label="中文" value="zh" />
            <el-option label="外文" value="en" />
          </el-select>
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="-"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="x"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleFilter">
            <el-icon><Search /></el-icon>
            <span>筛选</span>
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            <span>重置</span>
          </el-button>
        </el-form-item>

        <el-form-item style="margin-left: auto;">
          <el-button type="danger" @click="handleClearAll">
            <el-icon><Delete /></el-icon>
            <span>清空所有记录</span>
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 记录列表 -->
    <div v-if="allFilteredRecords.length > 0">
      <el-card
        v-for="record in filteredRecords"
        :key="record.id"
        class="record-item mb-20"
        shadow="hover"
      >
        <div class="record-content">
          <!-- 左侧：类型图标 -->
          <div class="record-icon">
            <el-icon :size="40" :color="getRecordColor(record.type)">
              <component :is="getRecordIcon(record.type)" />
            </el-icon>
          </div>

          <!-- 中间：记录信息 -->
          <div class="record-info">
            <div class="record-header">
              <el-tag :type="getRecordTypeTag(record.type)" size="large">
                {{ getRecordTypeName(record.type) }}
              </el-tag>
              <el-tag
                v-if="record.type === 'plagiarism'"
                :type="getEngineTagType(record.result?.engine)"
                size="small"
                effect="plain"
              >
                {{ getEngineLabel(record.result?.engine) }}
              </el-tag>
              <span class="record-title">{{ getRecordTitle(record) }}</span>
            </div>
            <div class="record-meta">
              <span class="meta-item">
                <el-icon><Clock /></el-icon>
                {{ formatDate(record.timestamp) }}
              </span>
              <span v-if="record.type === 'evaluation'" class="meta-item">
                <el-icon><TrendCharts /></el-icon>
                综合评分：<strong>{{ record.result.overall_score }}</strong>分
              </span>
            </div>
          </div>

          <!-- 右侧：操作按钮 -->
          <div class="record-actions">
            <el-button type="primary" @click="handleView(record)">
              <el-icon><View /></el-icon>
              <span>查看详情</span>
            </el-button>
            <el-button type="danger" @click="handleDelete(record.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="totalRecords"
          layout="total, prev, pager, next"
          background
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-icon class="empty-icon"><FolderOpened /></el-icon>
      <div class="empty-text">暂无历史记录</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Search,
  RefreshLeft,
  Delete,
  Clock,
  TrendCharts,
  View,
  FolderOpened,
  Edit,
  DocumentChecked,
  Document
} from '@element-plus/icons-vue'
import { useHistoryStore } from '@/store/modules/history'
import { useEvaluationStore } from '@/store/modules/evaluation'
import { useSpellCheckStore } from '@/store/modules/spellCheck'
import { useFormattingStore } from '@/store/modules/formatting'
import { usePlagiarismStore } from '@/store/modules/plagiarism'

const router = useRouter()
const historyStore = useHistoryStore()
const evaluationStore = useEvaluationStore()
const spellCheckStore = useSpellCheckStore()
const formattingStore = useFormattingStore()
const plagiarismStore = usePlagiarismStore()

// 分页
const currentPage = ref(1)
const pageSize = ref(10)

// 筛选表单
const filterForm = ref({
  type: '',
  engineLang: '',
  dateRange: null
})

// 当前应用的筛选条件
const appliedFilter = ref({
  type: '',
  engineLang: '',
  dateRange: null
})

/**
 * 筛选后的记录（全部）
 */
const allFilteredRecords = computed(() => {
  let records = [...historyStore.records]

  // 按类型筛选
  if (appliedFilter.value.type) {
    records = records.filter(r => r.type === appliedFilter.value.type)
  }

  // 按查重语种筛选（仅作用于查重记录）
  if (appliedFilter.value.engineLang) {
    records = records.filter(r => {
      if (r.type !== 'plagiarism') return false
      return getEngineLang(r.result?.engine) === appliedFilter.value.engineLang
    })
  }

  // 按日期范围筛选
  if (appliedFilter.value.dateRange && appliedFilter.value.dateRange.length === 2) {
    const startDate = Number(appliedFilter.value.dateRange[0])
    const endDate = Number(appliedFilter.value.dateRange[1]) + 86399999 // 加到当天23:59:59.999
    records = records.filter(
      r => r.timestamp >= startDate && r.timestamp <= endDate
    )
  }

  return records
})

/**
 * 当前页的记录
 */
const filteredRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return allFilteredRecords.value.slice(start, start + pageSize.value)
})

/**
 * 总记录数
 */
const totalRecords = computed(() => allFilteredRecords.value.length)

/**
 * 应用筛选
 */
function handleFilter() {
  currentPage.value = 1
  appliedFilter.value = {
    type: filterForm.value.type,
    engineLang: filterForm.value.engineLang,
    dateRange: filterForm.value.dateRange
  }
}

/**
 * 重置筛选
 */
function handleReset() {
  currentPage.value = 1
  filterForm.value = {
    type: '',
    engineLang: '',
    dateRange: null
  }
  appliedFilter.value = {
    type: '',
    engineLang: '',
    dateRange: null
  }
}

/**
 * 分页变化
 */
function handlePageChange(page) {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/**
 * 清空所有记录
 */
function handleClearAll() {
  ElMessageBox.confirm(
    '确定要清空所有历史记录吗？此操作不可恢复。',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(() => {
      historyStore.clearAllRecords()
      ElMessage.success('已清空所有记录')
    })
    .catch(() => {})
}

/**
 * 查看记录详情
 */
function handleView(record) {
  if (record.type === 'evaluation') {
    console.log('[History] 设置 pendingResult:', record.result)
    // 先访问 store 触发初始化
    const _ = evaluationStore.evaluationStatus
    evaluationStore.setPendingResult(record.result)
    console.log('[History] pendingResult 已设置，准备跳转')
    router.push({ path: '/evaluation', query: { from: 'history' } })
  } else if (record.type === 'spellcheck') {
    spellCheckStore.setPendingResult(record.result)
    router.push({ path: '/spell-check', query: { from: 'history' } })
  } else if (record.type === 'formatting') {
    formattingStore.setPendingResult(record.result)
    router.push({ path: '/formatting', query: { from: 'history' } })
  } else if (record.type === 'plagiarism') {
    plagiarismStore.setPendingResult(record.result)
    router.push({ path: '/plagiarism', query: { from: 'history' } })
  }
}

/**
 * 删除记录
 */
function handleDelete(id) {
  ElMessageBox.confirm('确定要删除这条记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => {
      historyStore.deleteRecord(id)
      ElMessage.success('删除成功')
    })
    .catch(() => {})
}

/**
 * 获取记录图标
 */
function getRecordIcon(type) {
  const iconMap = {
    evaluation: Edit,
    spellcheck: DocumentChecked,
    formatting: Document,
    plagiarism: Search
  }
  return iconMap[type] || Edit
}

/**
 * 获取记录颜色
 */
function getRecordColor(type) {
  const colorMap = {
    evaluation: 'rgb(0, 108, 73)',
    spellcheck: 'rgb(167, 139, 250)',
    formatting: 'rgb(18, 18, 18)',
    plagiarism: 'rgb(0, 108, 73)'
  }
  return colorMap[type] || 'rgb(107, 114, 128)'
}

/**
 * 获取记录类型标签颜色
 */
function getRecordTypeTag(type) {
  const tagMap = {
    evaluation: 'primary',
    spellcheck: 'success',
    formatting: 'warning',
    plagiarism: 'danger'
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
    formatting: '模板排版',
    plagiarism: '论文查重'
  }
  return nameMap[type] || '未知'
}

/**
 * 查重引擎 → 语种
 */
function getEngineLang(engine) {
  if (engine === 'english_academic' || engine === 'english_academic_fallback') {
    return 'en'
  }
  return 'zh'
}

/**
 * 查重引擎 → 中文标签
 */
function getEngineLabel(engine) {
  const map = {
    hybrid: '中文·AI语义',
    opensource: '中文·开源比对',
    english_academic: '外文·学术库',
    english_academic_fallback: '外文·降级',
  }
  return map[engine] || '中文·AI语义'
}

/**
 * 查重引擎 → 徽章色
 */
function getEngineTagType(engine) {
  if (engine === 'english_academic') return 'success'
  if (engine === 'english_academic_fallback') return 'warning'
  return 'info'
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
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.record-item {
  transition: all 0.3s;
}

.record-item:hover {
  transform: translateX(5px);
}

.record-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.record-icon {
  flex-shrink: 0;
}

.record-info {
  flex: 1;
  min-width: 0;
}

.record-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.record-title {
  font-size: 16px;
  font-weight: 500;
  color: rgb(18, 18, 18);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: rgb(107, 114, 128);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.record-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

@media screen and (max-width: 768px) {
  .record-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .record-actions {
    width: 100%;
  }

  .record-actions .el-button {
    flex: 1;
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 10px;
  margin-bottom: 20px;
}

.pagination-wrapper :deep(.el-pagination__total) {
  color: rgb(107, 114, 128);
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
</style>
