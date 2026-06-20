<template>
  <div class="src-card src-card--cn">
    <div class="src-title">{{ source.title || '未知来源' }}</div>
    <div class="src-meta">
      <span v-if="source.author">{{ source.author }}</span>
      <span v-if="source.year">· {{ source.year }}</span>
      <span v-if="similarity != null" class="src-sim">
        相似度 {{ (similarity * 100).toFixed(1) }}%
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  source: { type: Object, required: true },
  similarity: { type: Number, default: null },
})
</script>

<style scoped>
.src-card {
  padding: 10px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  margin-bottom: 8px;
}
.src-title {
  font-weight: 500;
  color: #111827;
  margin-bottom: 4px;
}
.src-meta {
  font-size: 12px;
  color: #6b7280;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.src-sim {
  margin-left: auto;
  color: #006c49;
  font-weight: 500;
}
</style>
