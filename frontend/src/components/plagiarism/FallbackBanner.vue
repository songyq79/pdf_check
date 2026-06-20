<template>
  <div class="fb-banner">
    <span class="fb-icon">!</span>
    <span class="fb-text">
      外部学术库暂不可用,已降级为 AI 基础模式。结果仅供参考,建议稍后重试。
    </span>
  </div>
</template>

<style scoped>
.fb-banner {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  margin-bottom: 12px;
  color: #78350f;
  font-size: 14px;
}
.fb-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #f59e0b;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}
</style>
