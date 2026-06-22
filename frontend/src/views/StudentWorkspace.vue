<template>
  <div class="stu-ws">
    <!-- 欢迎 -->
    <div class="hero">
      <div class="hero-text">
        <div class="hero-tag">📋 论文全流程 AI 助手</div>
        <div class="hero-title">你好，{{ authStore.username }}</div>
        <div class="hero-sub">从选题、文献、写作到评价、校对、排版、查重，全流程工具都在左侧。{{ isInstStudent ? '额度由学校统一提供。' : '' }}</div>
      </div>
      <div class="hero-emoji">🎓</div>
    </div>

    <!-- AI 新功能 -->
    <div class="section-label">✨ AI 助手 · 论文全程帮手</div>
    <div class="feat-grid feat-grid-3">
      <a v-for="f in aiFeatures" :key="f.key" class="feat-card featured" @click="go(f.to)">
        <div class="fc-icon" :style="{ background: f.bg }">{{ f.icon }}</div>
        <div class="fc-title">{{ f.title }}</div>
        <div class="fc-desc">{{ f.desc }}</div>
        <div class="fc-credits"><span class="cost">消耗 {{ costOf(f.cost) }} credits</span></div>
      </a>
    </div>

    <!-- 论文工具 -->
    <div class="section-label">🧰 论文工具</div>
    <div class="feat-grid feat-grid-4">
      <a v-for="f in toolFeatures" :key="f.key" class="feat-card-sm" @click="go(f.to)">
        <div class="fcs-icon">{{ f.icon }}</div>
        <div>
          <div class="fcs-title">{{ f.title }}</div>
          <div class="fcs-credits">{{ f.note }}</div>
        </div>
      </a>
    </div>

    <!-- 使用记录 + 占位 -->
    <div class="ws-row">
      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">我的使用记录</div>
          <span class="panel-action" @click="$router.push('/history')">全部 →</span>
        </div>
        <div class="panel-body" style="padding: 0 20px;">
          <div v-if="usageList.length" class="rec-list">
            <div v-for="(r, i) in usageList" :key="i" class="rec-item">
              <div class="rec-icon">{{ actionIcon(r.action) }}</div>
              <div class="rec-body">
                <div class="rec-title">{{ actionLabel(r.action) }}</div>
                <div class="rec-meta">{{ formatTime(r.created_at) }}</div>
              </div>
              <div class="rec-from">{{ sourceLabel(r.consumed_from) }}</div>
            </div>
          </div>
          <div v-else class="empty">还没有使用记录，从上方选一个功能开始吧</div>
        </div>
      </div>

      <div class="ws-right">
        <div class="panel placeholder">
          <div class="panel-head"><div class="panel-title">📍 论文进度路线图</div><span class="soon">即将上线</span></div>
          <div class="panel-body"><div class="ph-body">🗺️<div class="ph-text">选题→文献→写作→评价→校对→排版→查重→投稿 全流程引导，开发中</div></div></div>
        </div>
        <div class="panel placeholder">
          <div class="panel-head"><div class="panel-title">🏆 我的成就</div><span class="soon">即将上线</span></div>
          <div class="panel-body"><div class="ph-body">🎯<div class="ph-text">完成各阶段解锁徽章，开发中</div></div></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'
import { useBillingStore } from '@/store/modules/billing'
import * as billingApi from '@/api/billing'

const router = useRouter()
const authStore = useAuthStore()
const billingStore = useBillingStore()

const usageList = ref([])
const isInstStudent = computed(() => authStore.userType === 'institution_student')

const _ACTION = {
  evaluation: '智能评价', proofread: '论文校对', formatter: '模板排版', plagiarism: '论文查重',
  topic_evaluation: '选题评估', literature_review: '文献综述', writing_assist: '写作辅助',
  experiment_evaluation: '实验评审',
}
const _ICON = {
  evaluation: '⭐', proofread: '📝', formatter: '📐', plagiarism: '🔍',
  topic_evaluation: '🎯', literature_review: '📚', writing_assist: '✍️', experiment_evaluation: '🧪',
}
function actionLabel(k) { return _ACTION[k] || k }
function actionIcon(k) { return _ICON[k] || '•' }
function sourceLabel(s) {
  return { institution: '机构池', subscription: '包月', purchase: '购买', referral: '邀请', free: '免费', admin: '管理员' }[s] || s
}

function costOf(k) {
  const items = billingStore.featureCosts?.items || []
  const f = items.find(i => i.action === k)
  return f ? f.credits : '?'
}

const aiFeatures = [
  { key: 'topic_evaluation', title: '选题评估', desc: 'AI 评估创新性/可行性/重要性，帮你定一个好题目', cost: 'topic_evaluation', icon: '🎯', bg: '#FFF8E1', to: '/topic-evaluation' },
  { key: 'literature_review', title: '文献综述生成', desc: '检索学术库、主题分类，生成综述初稿+参考文献', cost: 'literature_review', icon: '📚', bg: '#E0F7FA', to: '/literature-review' },
  { key: 'writing_assist', title: '写作辅助', desc: '语法/逻辑/学术表达逐段润色，保留你的原始观点', cost: 'writing_assist', icon: '✍️', bg: '#F3E8FF', to: '/writing-assistant' },
]
const toolFeatures = [
  { key: 'evaluation', title: '智能评价', note: 'Word 报告 + 雷达图', icon: '⭐', to: '/evaluation' },
  { key: 'proofread', title: '论文校对', note: '修订标记返回', icon: '📝', to: '/spell-check' },
  { key: 'formatter', title: '模板排版', note: '一键套用格式', icon: '📐', to: '/formatting' },
  { key: 'plagiarism', title: '论文查重', note: '中文1 / 英文2', icon: '🔍', to: '/plagiarism' },
]

function go(to) { router.push(to) }

function formatTime(t) {
  if (!t) return ''
  try { return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }
  catch { return t }
}

onMounted(async () => {
  if (!billingStore.featureCosts) billingStore.loadFeatureCosts()
  try {
    const res = await billingApi.getUsageHistory()
    usageList.value = (res.data || []).slice(0, 8)
  } catch { /* ignore */ }
})
</script>

<style scoped>
.stu-ws { --green: #006C49; --muted: #7A8C82; --border: #E2EBE6; --text: #1A2E20;
  --green-pale: #E8F5EE; --green-pale2: #F0FAF5; --card-bg: #fff; --radius: 18px; --font-d: 'Newsreader', serif; }

.hero { background: linear-gradient(135deg, var(--green) 0%, #009962 50%, #00C47A 100%); border-radius: var(--radius);
  padding: 28px 32px; display: flex; align-items: center; gap: 24px; margin-bottom: 20px; position: relative; overflow: hidden; color: #fff; }
.hero-text { flex: 1; z-index: 1; }
.hero-tag { display: inline-block; font-size: 11px; font-weight: 700; background: rgba(255,255,255,0.20); padding: 3px 10px; border-radius: 100px; margin-bottom: 10px; }
.hero-title { font-family: var(--font-d); font-size: 26px; font-weight: 600; margin-bottom: 6px; }
.hero-sub { font-size: 14px; opacity: 0.8; line-height: 1.5; max-width: 460px; }
.hero-emoji { font-size: 64px; opacity: 0.25; position: absolute; right: 28px; bottom: 8px; }

.section-label { font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 12px; }

.feat-grid { display: grid; gap: 12px; margin-bottom: 22px; }
.feat-grid-3 { grid-template-columns: repeat(3, 1fr); }
.feat-grid-4 { grid-template-columns: repeat(4, 1fr); }
.feat-card { background: var(--card-bg); border-radius: var(--radius); border: 1px solid var(--border); padding: 20px 18px;
  box-shadow: 0 2px 16px rgba(0,60,40,0.07); cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; gap: 9px; }
.feat-card:hover { transform: translateY(-4px); box-shadow: 0 8px 32px rgba(0,108,73,0.14); border-color: rgba(0,108,73,0.25); }
.feat-card.featured { background: linear-gradient(135deg, #FAFFFE 0%, var(--green-pale2) 100%); border-color: rgba(0,108,73,0.25); }
.fc-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.fc-title { font-size: 14px; font-weight: 700; color: var(--text); }
.fc-desc { font-size: 12px; color: var(--muted); line-height: 1.5; flex: 1; }
.fc-credits { font-size: 11px; margin-top: auto; }
.fc-credits .cost { font-weight: 700; color: var(--green); }

.feat-card-sm { background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); padding: 14px 16px;
  box-shadow: 0 2px 16px rgba(0,60,40,0.07); cursor: pointer; transition: all 0.18s; display: flex; align-items: center; gap: 12px; }
.feat-card-sm:hover { border-color: rgba(0,108,73,0.25); background: var(--green-pale2); }
.fcs-icon { font-size: 22px; }
.fcs-title { font-size: 13px; font-weight: 700; color: var(--text); }
.fcs-credits { font-size: 11px; color: var(--muted); }

.ws-row { display: grid; grid-template-columns: 1fr 340px; gap: 16px; }
.ws-right { display: flex; flex-direction: column; gap: 14px; }
.panel { background: var(--card-bg); border-radius: var(--radius); border: 1px solid var(--border); box-shadow: 0 2px 16px rgba(0,60,40,0.07); overflow: hidden; }
.panel-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border); }
.panel-title { font-size: 14px; font-weight: 700; color: var(--text); }
.panel-action { font-size: 12px; color: var(--green); cursor: pointer; font-weight: 600; }
.panel-body { padding: 20px; }
.empty { font-size: 13px; color: rgb(156,163,175); text-align: center; padding: 28px; }

.rec-list { display: flex; flex-direction: column; }
.rec-item { display: flex; align-items: center; gap: 14px; padding: 13px 0; border-bottom: 1px solid var(--border); }
.rec-item:last-child { border-bottom: none; }
.rec-icon { width: 38px; height: 38px; border-radius: 10px; background: var(--green-pale); display: flex; align-items: center; justify-content: center; font-size: 17px; flex-shrink: 0; }
.rec-body { flex: 1; min-width: 0; }
.rec-title { font-size: 13px; font-weight: 600; color: var(--text); }
.rec-meta { font-size: 11px; color: var(--muted); margin-top: 2px; }
.rec-from { font-size: 11px; color: var(--muted); background: var(--green-pale2); padding: 2px 8px; border-radius: 100px; }

.panel.placeholder { opacity: 0.9; }
.soon { font-size: 11px; background: var(--green-pale); color: var(--green); padding: 2px 8px; border-radius: 100px; font-weight: 600; }
.ph-body { text-align: center; padding: 24px 12px; color: var(--muted); font-size: 28px; }
.ph-text { font-size: 12px; margin-top: 8px; line-height: 1.5; }

@media (max-width: 820px) {
  .feat-grid-3, .feat-grid-4 { grid-template-columns: repeat(2, 1fr); }
  .ws-row { grid-template-columns: 1fr; }
}
</style>
