<template>
  <div class="page-container">
    <div class="page-title">机构管理控制台</div>
    <div class="page-description" v-if="info">{{ info.name }} · {{ levelLabel(info.subscription_level) }}</div>

    <div v-if="loadError">
      <el-result icon="warning" title="无法加载机构数据" :sub-title="loadError">
        <template #extra><el-button @click="loadAll">重试</el-button></template>
      </el-result>
    </div>

    <template v-else>
      <!-- KPI -->
      <div class="kpi-grid mb-20" v-if="stats">
        <el-card class="kpi"><div class="kpi-num">{{ stats.students.total }}</div><div class="kpi-label">学生总数</div></el-card>
        <el-card class="kpi"><div class="kpi-num">{{ stats.students.pending }}</div><div class="kpi-label">待审批</div></el-card>
        <el-card class="kpi"><div class="kpi-num">{{ stats.quota.used }}<span class="kpi-sub">/{{ stats.quota.total }}</span></div><div class="kpi-label">配额已用</div></el-card>
        <el-card class="kpi"><div class="kpi-num">{{ stats.total_usage }}</div><div class="kpi-label">总使用次数</div></el-card>
      </div>

      <!-- 配额进度 + 邀请码 -->
      <el-card class="mb-20" v-if="stats && info">
        <div class="quota-row">
          <div style="flex:1">
            <div class="block-title">配额池</div>
            <el-progress :percentage="quotaPct" :stroke-width="14" :color="quotaColor" />
            <div class="quota-hint">剩余 {{ stats.quota.remaining }} / {{ stats.quota.total }} 次</div>
          </div>
          <div class="invite-box">
            <div class="invite-label">学生注册邀请码</div>
            <div class="invite-code">{{ info.invite_code }}</div>
          </div>
        </div>
      </el-card>

      <!-- 用量分布 -->
      <div class="dist-grid mb-20" v-if="stats">
        <el-card>
          <div class="block-title">按功能用量</div>
          <div v-for="(v,k) in stats.usage_by_action" :key="k" class="dist-item">
            <span>{{ actionLabel(k) }}</span><strong>{{ v }}</strong>
          </div>
          <div v-if="!Object.keys(stats.usage_by_action).length" class="empty">暂无使用记录</div>
        </el-card>
        <el-card>
          <div class="block-title">按学院用量</div>
          <div v-for="(v,k) in stats.usage_by_college" :key="k" class="dist-item">
            <span>{{ k }}</span><strong>{{ v }}</strong>
          </div>
          <div v-if="!Object.keys(stats.usage_by_college).length" class="empty">暂无使用记录</div>
        </el-card>
      </div>

      <!-- 学生列表 -->
      <el-card>
        <div class="students-header">
          <div class="block-title">学生列表</div>
          <div>
            <el-button size="small" @click="downloadReport">导出报表 CSV</el-button>
          </div>
        </div>
        <el-table :data="students" size="small" style="width:100%" max-height="420">
          <el-table-column prop="student_id" label="学号" width="110" />
          <el-table-column prop="username" label="用户名" width="140" />
          <el-table-column prop="college" label="学院" width="110" />
          <el-table-column prop="grade" label="年级" width="80" />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status==='approved'?'success':'warning'" size="small">{{ row.status==='approved'?'已通过':'待审批' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button v-if="row.status!=='approved'" type="primary" size="small" link @click="approve(row)">审批通过</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!students.length" class="empty" style="padding:20px;text-align:center">暂无学生，把邀请码发给学生注册，或用「批量导入」</div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import instAPI from '@/api/institution'

const info = ref(null)
const stats = ref(null)
const students = ref([])
const loadError = ref('')

const _ACTION = {
  evaluation: '智能评价', proofread: '论文校对', formatter: '模板排版', plagiarism: '论文查重',
  topic_evaluation: '选题评估', literature_review: '文献综述', writing_assist: '写作辅助',
  experiment_evaluation: '实验评审',
}
function actionLabel(k) { return _ACTION[k] || k }
function levelLabel(l) { return { small: '小规模版', medium: '中规模版', large: '大规模版' }[l] || l }

const quotaPct = computed(() => {
  if (!stats.value || !stats.value.quota.total) return 0
  return Math.min(100, Math.round(stats.value.quota.used / stats.value.quota.total * 100))
})
const quotaColor = computed(() => quotaPct.value >= 90 ? '#dc2626' : quotaPct.value >= 70 ? '#d97706' : '#006C49')

async function loadAll() {
  loadError.value = ''
  try {
    const [i, d, s] = await Promise.all([instAPI.info(), instAPI.dashboard(), instAPI.students()])
    info.value = i
    stats.value = d
    students.value = s.students || []
  } catch (e) {
    loadError.value = e._userMessage || '需要机构管理员权限'
  }
}

async function approve(row) {
  try {
    await instAPI.approveStudent(row.user_id)
    ElMessage.success('已审批通过')
    await loadAll()
  } catch (e) { /* 拦截器处理 */ }
}

async function downloadReport() {
  try {
    await instAPI.downloadReport()
    ElMessage.success('开始下载报表')
  } catch (e) { ElMessage.error('导出失败') }
}

onMounted(loadAll)
</script>

<style scoped>
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
@media (max-width: 800px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
.kpi { text-align: center; }
.kpi-num { font-size: 32px; font-weight: 700; color: #006C49; }
.kpi-sub { font-size: 16px; color: rgb(156,163,175); }
.kpi-label { font-size: 13px; color: rgb(107,114,128); margin-top: 4px; }

.quota-row { display: flex; gap: 24px; align-items: center; flex-wrap: wrap; }
.quota-hint { font-size: 12px; color: rgb(107,114,128); margin-top: 6px; }
.invite-box { text-align: center; }
.invite-label { font-size: 12px; color: rgb(107,114,128); }
.invite-code { font-size: 22px; font-weight: 700; color: #006C49; font-family: monospace; letter-spacing: 2px; }

.dist-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 800px) { .dist-grid { grid-template-columns: 1fr; } }
.dist-item { display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid rgba(0,0,0,.05); font-size: 14px; color: rgb(55,65,81); }
.dist-item strong { color: #006C49; }
.empty { font-size: 13px; color: rgb(156,163,175); }

.block-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; }
.students-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }

:deep(.el-card) { border-radius: 20px; border: 1px solid rgba(229,231,235,0.5); box-shadow: 0 4px 32px rgba(0,0,0,0.06); }
:deep(.el-button--primary) { background: rgb(0,108,73); border-color: rgb(0,108,73); }
</style>
