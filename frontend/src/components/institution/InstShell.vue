<template>
  <InstLayout
    variant="student"
    brand-sub="学生工作台"
    :nav-groups="navGroups"
    :page-title="pageTitle"
    :breadcrumb="breadcrumb"
    :user-name="authStore.username"
    :user-role="myInst ? myInst.institution_name : '机构学生'"
    @nav="onNav"
  >
    <template #sidebar-extra>
      <div class="sb-quota">
        <div class="sq-label">{{ myInst ? '机构配额池' : '我的剩余额度' }}</div>
        <div class="sq-num">{{ remaining }} <span>credits</span></div>
        <div class="sq-track"><div class="sq-fill" :style="{ width: fillPct + '%' }"></div></div>
        <div class="sq-hint">{{ hint }}</div>
      </div>
    </template>

    <router-view />
  </InstLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'
import { useBillingStore } from '@/store/modules/billing'
import instAPI from '@/api/institution'
import InstLayout from './InstLayout.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const billingStore = useBillingStore()

const myInst = ref(null)

const pageTitle = computed(() => route.meta.title || '工作台')
const breadcrumb = computed(() => (myInst.value ? myInst.value.institution_name : '机构') + ' / ' + pageTitle.value)

const remaining = computed(() => myInst.value ? myInst.value.quota_remaining : billingStore.totalCredits)
const fillPct = computed(() => {
  if (myInst.value && myInst.value.quota_total) {
    return Math.min(100, Math.round(myInst.value.quota_remaining / myInst.value.quota_total * 100))
  }
  return remaining.value > 0 ? Math.min(100, remaining.value * 5) : 0
})
const hint = computed(() => myInst.value ? `机构共 ${myInst.value.quota_total} credits` : '按功能消耗不同 credits')

// 导航项（active 跟随当前路由）
const navGroups = computed(() => {
  const p = route.path
  return [
    { label: '工作台', items: [
      { icon: '🏠', text: '我的主页', to: '/workspace', active: p === '/workspace' },
      { icon: '📄', text: '历史记录', to: '/history', active: p === '/history' },
    ] },
    { label: 'AI 助手（新）', items: [
      { icon: '🎯', text: '选题评估', to: '/topic-evaluation', active: p === '/topic-evaluation' },
      { icon: '📚', text: '文献综述', to: '/literature-review', active: p === '/literature-review' },
      { icon: '✍️', text: '写作辅助', to: '/writing-assistant', active: p === '/writing-assistant' },
      { icon: '🧪', text: '实验评审', to: '/experiment-review', active: p === '/experiment-review' },
    ] },
    { label: '论文工具', items: [
      { icon: '⭐', text: '智能评价', to: '/evaluation', active: p === '/evaluation' },
      { icon: '📝', text: '论文校对', to: '/spell-check', active: p === '/spell-check' },
      { icon: '📐', text: '模板排版', to: '/formatting', active: p === '/formatting' },
      { icon: '🔍', text: '论文查重', to: '/plagiarism', active: p === '/plagiarism' },
      { icon: '📰', text: '投稿选刊', to: '/journal-select', active: p === '/journal-select' },
    ] },
  ]
})

function onNav(item) {
  if (item.active || !item.to) return
  router.push(item.to)
}

onMounted(async () => {
  if (!billingStore.featureCosts) billingStore.loadFeatureCosts()
  billingStore.loadQuota()
  try { myInst.value = await instAPI.my() } catch { /* 未绑定机构则用个人额度 */ }
})
</script>

<style scoped>
.sb-quota { margin: 10px 12px; background: #F0FAF5; border-radius: 12px; padding: 14px; border: 1px solid rgba(0,108,73,0.12); }
.sq-label { font-size: 11px; color: #7A8C82; font-weight: 600; margin-bottom: 8px; }
.sq-num { font-family: 'Newsreader', serif; font-size: 26px; font-weight: 600; color: #006C49; line-height: 1; margin-bottom: 8px; }
.sq-num span { font-size: 13px; font-weight: 400; color: #7A8C82; }
.sq-track { background: #E2EBE6; border-radius: 100px; height: 6px; overflow: hidden; margin-bottom: 8px; }
.sq-fill { height: 100%; background: #006C49; border-radius: 100px; }
.sq-hint { font-size: 11px; color: #7A8C82; }
</style>
