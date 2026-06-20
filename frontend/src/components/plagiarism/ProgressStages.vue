<template>
  <div class="ps-wrap">
    <div class="ps-bar">
      <div class="ps-fill" :style="{ width: progress + '%' }"></div>
    </div>
    <div class="ps-text">
      <span class="ps-pct">{{ progress }}%</span>
      <span v-if="stage" class="ps-stage">{{ stage }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  progress: { type: Number, default: 0 },
  stage: { type: String, default: '' },
})
</script>

<style scoped>
.ps-wrap { width: 100%; }
.ps-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}
.ps-fill {
  height: 100%;
  background: linear-gradient(90deg, #006c49, #10b981);
  transition: width 0.3s ease;
}
.ps-text {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.ps-pct {
  color: #006c49;
  font-weight: 600;
}
.ps-stage {
  color: #6b7280;
}
</style>
