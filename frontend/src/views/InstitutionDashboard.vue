<template>
  <div class="inst-dash-page">
    <!-- 加载失败 -->
    <div v-if="loadError" class="dash-error">
      <el-result icon="warning" title="无法加载机构数据" :sub-title="loadError">
        <template #extra><el-button @click="loadAll">重试</el-button></template>
      </el-result>
    </div>

    <InstLayout
      v-else
      variant="admin"
      :brand-sub="info ? info.name + ' 管理控制台' : '机构管理控制台'"
      :nav-groups="navGroups"
      page-title="工作台"
      :breadcrumb="(info ? info.name : '机构') + ' / 管理控制台'"
      :user-name="info ? info.name : '机构'"
      user-role="机构管理员"
      @nav="onNav"
    >
      <template #actions>
        <el-button size="small" @click="downloadReport">导出报表</el-button>
        <el-button size="small" type="primary" @click="loadAll">刷新</el-button>
      </template>

      <!-- 配额预警 -->
      <div v-if="quotaPct >= 80" class="alert-banner">
        ⚠️&nbsp;<strong>配额预警：</strong>机构配额池已用 {{ quotaPct }}%，剩余 {{ stats ? stats.quota.remaining : 0 }} 次，建议尽快补充。
      </div>

      <!-- KPI -->
      <div class="kpi-row" v-if="stats">
        <div class="kpi-card green">
          <div class="kpi-label">学生总数</div>
          <div class="kpi-value">{{ stats.students.total }}<small> 人</small></div>
          <div class="kpi-trend">已通过 {{ stats.students.approved }} 人</div>
        </div>
        <div class="kpi-card orange">
          <div class="kpi-label">待审批</div>
          <div class="kpi-value">{{ stats.students.pending }}<small> 人</small></div>
          <div class="kpi-trend">在「学生审批」处理</div>
        </div>
        <div class="kpi-card blue">
          <div class="kpi-label">配额已用</div>
          <div class="kpi-value">{{ stats.quota.used }}<small> /{{ stats.quota.total }}</small></div>
          <div class="kpi-trend">剩余 {{ stats.quota.remaining }} 次</div>
        </div>
        <div class="kpi-card red">
          <div class="kpi-label">总使用次数</div>
          <div class="kpi-value">{{ stats.total_usage }}<small> 次</small></div>
          <div class="kpi-trend">全机构累计</div>
        </div>
      </div>

      <!-- 趋势 + 按功能用量 -->
      <div class="panel-row" style="grid-template-columns: 3fr 2fr;" v-if="stats">
        <div class="panel">
          <div class="panel-head">
            <div>
              <div class="panel-title">近 30 天用量趋势</div>
              <div class="panel-sub">全机构每日使用次数</div>
            </div>
          </div>
          <div class="panel-body">
            <div v-if="trendBars.length" class="chart-wrap">
              <div v-for="(b, i) in trendBars" :key="i" class="chart-col">
                <div class="chart-bar-wrap">
                  <div class="chart-bar" :style="{ height: b.h + '%' }" :title="b.date + '：' + b.v + ' 次'"></div>
                </div>
                <div class="chart-label">{{ b.label }}</div>
              </div>
            </div>
            <div v-else class="empty">暂无使用记录</div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">按功能用量</div>
          </div>
          <div class="panel-body">
            <div v-if="actionRows.length" class="dist-list">
              <div v-for="r in actionRows" :key="r.key" class="dist-item">
                <span class="dist-name">{{ r.label }}</span>
                <div class="dist-bar-wrap"><div class="dist-bar" :style="{ width: r.pct + '%' }"></div></div>
                <strong class="dist-val">{{ r.v }}</strong>
              </div>
            </div>
            <div v-else class="empty">暂无使用记录</div>
          </div>
        </div>
      </div>

      <!-- 按学院用量 + 配额池/邀请码 -->
      <div class="panel-row" style="grid-template-columns: 3fr 2fr;" v-if="stats && info">
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">按学院用量</div>
          </div>
          <div class="panel-body" style="padding-top: 12px;">
            <table class="dept-table" v-if="collegeRows.length">
              <thead><tr><th>学院</th><th>使用次数</th><th>占比</th></tr></thead>
              <tbody>
                <tr v-for="r in collegeRows" :key="r.name">
                  <td><span class="dept-dot" :style="{ background: r.color }"></span>{{ r.name }}</td>
                  <td>{{ r.v }}</td>
                  <td>
                    <span class="quota-bar-wrap"><span class="quota-bar-fill" :style="{ width: r.pct + '%' }"></span></span>
                    <span class="dept-pct">{{ r.pct }}%</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty">暂无使用记录</div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-head"><div class="panel-title">配额池 · 邀请码</div></div>
          <div class="panel-body">
            <div class="quota-gauge">
              <div class="qg-num">{{ quotaPct }}<span>%</span></div>
              <div class="qg-hint">已用 {{ stats.quota.used }} / {{ stats.quota.total }} 次</div>
              <div class="qg-track"><div class="qg-fill" :class="quotaClass" :style="{ width: quotaPct + '%' }"></div></div>
            </div>
            <div class="invite-box">
              <div class="invite-label">学生注册邀请码</div>
              <div class="invite-code" @click="copyInvite">{{ info.invite_code }} <span class="copy-hint">点击复制</span></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 学生列表 -->
      <div class="panel" v-if="stats">
        <div class="panel-head">
          <div class="panel-title">学生列表 <span class="title-count" v-if="pendingCount">{{ pendingCount }} 待审批</span></div>
          <span class="panel-action" @click="downloadReport">导出报表 CSV</span>
        </div>
        <div class="panel-body" style="padding-top: 8px;">
          <el-table :data="students" size="small" style="width:100%" max-height="420">
            <el-table-column prop="student_id" label="学号" width="120" />
            <el-table-column prop="username" label="用户名" width="150" />
            <el-table-column prop="college" label="学院" width="120" />
            <el-table-column prop="grade" label="年级" width="90" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'approved' ? 'success' : 'warning'" size="small">
                  {{ row.status === 'approved' ? '已通过' : '待审批' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="{ row }">
                <el-button v-if="row.status !== 'approved'" type="primary" size="small" link @click="approve(row)">审批通过</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!students.length" class="empty" style="padding:20px;text-align:center">
            暂无学生，把邀请码发给学生注册即可
          </div>
        </div>
      </div>

      <!-- 占位板块（即将上线） -->
      <div class="panel-row" style="grid-template-columns: 1fr 1fr 1fr;">
        <div class="panel placeholder" v-for="p in placeholders" :key="p.title">
          <div class="panel-head"><div class="panel-title">{{ p.title }}</div><span class="soon">即将上线</span></div>
          <div class="panel-body"><div class="ph-body">{{ p.icon }}<div class="ph-text">{{ p.desc }}</div></div></div>
        </div>
      </div>
    </InstLayout>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import instAPI from '@/api/institution'
import InstLayout from '@/components/institution/InstLayout.vue'

const route = useRoute()
// 系统管理员从机构列表「进入控制台」带 ?id=；机构管理员自己进则为空
const instId = computed(() => route.query.id ? Number(route.query.id) : undefined)

const info = ref(null)
const stats = ref(null)
const students = ref([])
const loadError = ref('')

const _ACTION = {
  evaluation: '智能评价', proofread: '论文校对', formatter: '模板排版', plagiarism: '论文查重',
  topic_evaluation: '选题评估', literature_review: '文献综述',
  writing_assist: '写作辅助（单段）', writing_whole: '写作辅助（整篇）',
  experiment_evaluation: '实验评审',
}
function actionLabel(k) { return _ACTION[k] || k }

const _COLORS = ['#006C49', '#2563EB', '#9333EA', '#E8840A', '#DC3545', '#0077A8', '#16A34A']

const pendingCount = computed(() => stats.value ? stats.value.students.pending : 0)

const quotaPct = computed(() => {
  if (!stats.value || !stats.value.quota.total) return 0
  return Math.min(100, Math.round(stats.value.quota.used / stats.value.quota.total * 100))
})
const quotaClass = computed(() => quotaPct.value >= 90 ? 'danger' : quotaPct.value >= 70 ? 'warn' : '')

// 按功能用量
const actionRows = computed(() => {
  if (!stats.value) return []
  const m = stats.value.usage_by_action || {}
  const entries = Object.entries(m)
  if (!entries.length) return []
  const max = Math.max(...entries.map(e => e[1]))
  return entries.sort((a, b) => b[1] - a[1]).map(([k, v]) => ({
    key: k, label: actionLabel(k), v, pct: max ? Math.round(v / max * 100) : 0,
  }))
})

// 按学院用量
const collegeRows = computed(() => {
  if (!stats.value) return []
  const m = stats.value.usage_by_college || {}
  const entries = Object.entries(m)
  if (!entries.length) return []
  const total = entries.reduce((s, e) => s + e[1], 0)
  return entries.sort((a, b) => b[1] - a[1]).map(([k, v], i) => ({
    name: k, v, pct: total ? Math.round(v / total * 100) : 0, color: _COLORS[i % _COLORS.length],
  }))
})

// 近30天趋势
const trendBars = computed(() => {
  if (!stats.value) return []
  const m = stats.value.usage_trend || {}
  const dates = Object.keys(m).sort()
  if (!dates.length) return []
  const recent = dates.slice(-14)
  const max = Math.max(...recent.map(d => m[d]))
  return recent.map(d => ({
    date: d,
    label: d.slice(5),  // MM-DD
    v: m[d],
    h: max ? Math.max(6, Math.round(m[d] / max * 100)) : 6,
  }))
})

const placeholders = [
  { title: '评分分布', icon: '📊', desc: '全机构论文评价分数段分布，开发中' },
  { title: '论文动态', icon: '📄', desc: '最新论文处理动态流，开发中' },
  { title: '系统消息', icon: '🔔', desc: '配额预警、功能上新等通知，开发中' },
]

const navGroups = computed(() => [
  { label: '概览', items: [{ icon: '🏠', text: '工作台', active: true, key: 'home' }] },
  {
    label: '机构管理', items: [
      { icon: '👥', text: '学生审批', key: 'students', badge: pendingCount.value || undefined, badgeType: 'orange' },
      { icon: '📈', text: '使用统计', key: 'stats' },
      { icon: '🎫', text: '邀请码', key: 'invite' },
    ],
  },
  { label: '设置', items: [{ icon: '⚙️', text: '机构设置', key: 'settings' }] },
])

function onNav(item) {
  if (item.key === 'home' || item.active) return
  if (item.key === 'invite') { copyInvite(); return }
  ElMessage.info('「' + item.text + '」即将上线')
}

async function loadAll() {
  loadError.value = ''
  try {
    const [i, d, s] = await Promise.all([
      instAPI.info(instId.value), instAPI.dashboard(instId.value), instAPI.students(undefined, instId.value),
    ])
    info.value = i
    stats.value = d
    students.value = s.students || []
  } catch (e) {
    loadError.value = e._userMessage || '需要机构管理员权限'
  }
}

async function approve(row) {
  try {
    await instAPI.approveStudent(row.user_id, instId.value)
    ElMessage.success('已审批通过')
    await loadAll()
  } catch (e) { /* 拦截器处理 */ }
}

async function copyInvite() {
  if (!info.value) return
  try {
    await navigator.clipboard.writeText(info.value.invite_code)
    ElMessage.success('已复制邀请码：' + info.value.invite_code)
  } catch {
    ElMessage.info('邀请码：' + info.value.invite_code)
  }
}

async function downloadReport() {
  try {
    await instAPI.downloadReport(instId.value)
    ElMessage.success('开始下载报表')
  } catch (e) { ElMessage.error('导出失败') }
}

onMounted(loadAll)
</script>

<style scoped>
.inst-dash-page { --green: #006C49; --orange: #E8840A; --red: #DC3545; --blue: #2563EB;
  --muted: #7A8C82; --border: #E2EBE6; --text: #1A2E20; --green-pale: #E8F5EE; --green-pale2: #F0FAF5;
  --card-bg: #fff; --radius: 16px; --font-d: 'Newsreader', serif; }

.dash-error { padding: 40px; }

/* 复用 mockup 视觉 */
.alert-banner {
  background: #FFF8EC; border: 1px solid #F5C87A; border-radius: 10px;
  padding: 10px 16px; margin-bottom: 20px; font-size: 13px; color: #7A5A00;
}
.alert-banner strong { color: #5A4000; }

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.kpi-card {
  background: var(--card-bg); border-radius: var(--radius); border: 1px solid var(--border);
  padding: 20px 22px; box-shadow: 0 2px 16px rgba(0,60,40,0.08); position: relative; overflow: hidden;
}
.kpi-card::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.kpi-card.green::after { background: var(--green); }
.kpi-card.orange::after { background: var(--orange); }
.kpi-card.blue::after { background: var(--blue); }
.kpi-card.red::after { background: var(--red); }
.kpi-label { font-size: 12px; color: var(--muted); font-weight: 600; margin-bottom: 8px; }
.kpi-value { font-family: var(--font-d); font-size: 34px; font-weight: 600; line-height: 1; color: var(--text); margin-bottom: 6px; }
.kpi-value small { font-size: 17px; font-weight: 400; color: var(--muted); }
.kpi-trend { font-size: 12px; color: var(--muted); }

.panel-row { display: grid; gap: 16px; margin-bottom: 20px; }
.panel {
  background: var(--card-bg); border-radius: var(--radius); border: 1px solid var(--border);
  box-shadow: 0 2px 16px rgba(0,60,40,0.08); overflow: hidden;
}
.panel-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
}
.panel-title { font-size: 14px; font-weight: 700; color: var(--text); }
.title-count { font-size: 11px; background: #FEE9CE; color: #C25900; padding: 2px 8px; border-radius: 100px; margin-left: 6px; font-weight: 600; }
.panel-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
.panel-action { font-size: 12px; color: var(--green); cursor: pointer; font-weight: 600; }
.panel-body { padding: 20px; }
.empty { font-size: 13px; color: rgb(156,163,175); text-align: center; padding: 24px; }

/* 趋势柱状 */
.chart-wrap { height: 160px; display: flex; align-items: flex-end; gap: 8px; }
.chart-col { display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1; }
.chart-bar-wrap { flex: 1; display: flex; align-items: flex-end; width: 100%; }
.chart-bar { width: 100%; border-radius: 5px 5px 0 0; background: var(--green); transition: all 0.3s; min-height: 4px; }
.chart-bar:hover { background: #00875C; }
.chart-label { font-size: 10px; color: var(--muted); }

/* 按功能用量 */
.dist-list { display: flex; flex-direction: column; gap: 12px; }
.dist-item { display: flex; align-items: center; gap: 10px; }
.dist-name { font-size: 13px; color: var(--text); width: 78px; flex-shrink: 0; }
.dist-bar-wrap { flex: 1; background: var(--green-pale); border-radius: 100px; height: 10px; overflow: hidden; }
.dist-bar { height: 100%; border-radius: 100px; background: var(--green); }
.dist-val { font-size: 13px; color: var(--green); width: 40px; text-align: right; }

/* 学院表 */
.dept-table { width: 100%; border-collapse: collapse; }
.dept-table th { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase;
  padding: 0 0 10px; text-align: left; border-bottom: 1px solid var(--border); }
.dept-table td { padding: 11px 0; font-size: 13px; color: var(--text); border-bottom: 1px solid var(--border); }
.dept-table tr:last-child td { border-bottom: none; }
.dept-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
.quota-bar-wrap { width: 90px; background: var(--border); border-radius: 100px; height: 6px; display: inline-block; overflow: hidden; vertical-align: middle; }
.quota-bar-fill { height: 100%; border-radius: 100px; background: var(--green); display: block; }
.dept-pct { font-size: 11px; color: var(--muted); margin-left: 8px; }

/* 配额池 gauge */
.quota-gauge { text-align: center; padding: 8px 0 16px; }
.qg-num { font-family: var(--font-d); font-size: 44px; font-weight: 600; color: var(--green); line-height: 1; }
.qg-num span { font-size: 22px; color: var(--muted); }
.qg-hint { font-size: 12px; color: var(--muted); margin: 6px 0 12px; }
.qg-track { width: 70%; margin: 0 auto; background: var(--border); border-radius: 100px; height: 8px; overflow: hidden; }
.qg-fill { height: 100%; border-radius: 100px; background: var(--green); }
.qg-fill.warn { background: var(--orange); }
.qg-fill.danger { background: var(--red); }
.invite-box { text-align: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border); }
.invite-label { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
.invite-code { font-size: 22px; font-weight: 700; color: var(--green); font-family: monospace; letter-spacing: 2px; cursor: pointer; }
.copy-hint { font-size: 11px; color: var(--muted); font-family: var(--font); letter-spacing: 0; font-weight: 400; margin-left: 6px; }

/* 占位 */
.panel.placeholder { opacity: 0.85; }
.soon { font-size: 11px; background: var(--green-pale); color: var(--green); padding: 2px 8px; border-radius: 100px; font-weight: 600; }
.ph-body { text-align: center; padding: 24px 12px; color: var(--muted); font-size: 28px; }
.ph-text { font-size: 12px; margin-top: 8px; line-height: 1.5; }
</style>
