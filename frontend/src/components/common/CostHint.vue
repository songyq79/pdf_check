<template>
  <!-- 仅在开启计费时展示；关闭计费=全部免费，不显示以免误导 -->
  <div v-if="billingStore.billingEnabled && credits > 0" class="cost-hint" :class="{ insufficient }">
    <span class="cost-part">本次消耗 <strong>{{ credits }}</strong> credit{{ credits > 1 ? 's' : '' }}</span>
    <template v-if="quotaLoaded">
      <span class="sep">·</span>
      <span class="remain-part">剩余 <strong>{{ remaining }}</strong></span>
      <span v-if="insufficient" class="warn">额度不足，请先充值</span>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useBillingStore } from '@/store/modules/billing'

const props = defineProps({
  // 功能 action（对应后端 FEATURE_COSTS 的键），用于查表
  action: { type: String, default: '' },
  // 直接指定消耗（查重等按语言动态计算时用）；>=0 时优先于 action
  credits: { type: Number, default: -1 },
})

const billingStore = useBillingStore()

// 本次消耗：显式 credits 优先，否则按 action 查表
const credits = computed(() => {
  if (props.credits >= 0) return props.credits
  const items = billingStore.featureCosts?.items || []
  const found = items.find(i => i.action === props.action)
  return found ? found.credits : 0
})

const quotaLoaded = computed(() => billingStore.quota != null)
const remaining = computed(() => billingStore.totalCredits)
const insufficient = computed(() => quotaLoaded.value && remaining.value < credits.value)

onMounted(() => {
  if (!billingStore.featureCosts) billingStore.loadFeatureCosts()
  if (!billingStore.pricing) billingStore.loadPricing()
  if (!billingStore.quota) billingStore.loadQuota()
})
</script>

<style scoped>
.cost-hint {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(0, 108, 73, 0.06);
  border: 1px solid rgba(0, 108, 73, 0.18);
  border-radius: 10px;
  color: rgb(59, 74, 65);
  font-size: 13px;
  line-height: 20px;
}

.cost-hint.insufficient {
  background: rgba(220, 38, 38, 0.06);
  border-color: rgba(220, 38, 38, 0.3);
}

.cost-hint strong {
  color: rgb(0, 108, 73);
  font-weight: 600;
}

.cost-hint.insufficient strong {
  color: rgb(220, 38, 38);
}

.sep {
  color: rgba(59, 74, 65, 0.4);
}

.warn {
  color: rgb(220, 38, 38);
  font-weight: 500;
}
</style>
