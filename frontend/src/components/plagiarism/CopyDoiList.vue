<template>
  <div v-if="validSources.length" class="cdl-wrap">
    <button class="cdl-btn" @click="copy">
      <span class="cdl-icon">≡</span>
      复制 DOI 清单 ({{ validSources.length }})
    </button>
    <span v-if="copied" class="cdl-toast">已复制到剪贴板</span>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  sources: { type: Array, default: () => [] },
})

const copied = ref(false)

const validSources = computed(() =>
  props.sources.filter(s => s.doi)
)

async function copy() {
  const md = validSources.value.map(s => {
    const author = s.author ? ` — ${s.author}` : ''
    const year = s.year ? `, ${s.year}` : ''
    return `- [${s.title}](https://doi.org/${s.doi})${author}${year}`
  }).join('\n')
  try {
    await navigator.clipboard.writeText(md)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1800)
  } catch (e) {
    console.warn('[copyDoi] 复制失败', e)
  }
}
</script>

<style scoped>
.cdl-wrap {
  display: flex;
  gap: 10px;
  align-items: center;
  margin: 12px 0;
}
.cdl-btn {
  padding: 8px 14px;
  background: #fff;
  border: 1px solid #006c49;
  color: #006c49;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.cdl-btn:hover { background: #006c49; color: #fff; }
.cdl-icon { font-weight: 700; }
.cdl-toast {
  font-size: 12px;
  color: #059669;
}
</style>
