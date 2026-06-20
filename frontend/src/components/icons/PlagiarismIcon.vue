<template>
  <svg
    viewBox="0 0 48 48"
    width="1em"
    height="1em"
    fill="currentColor"
    class="plagiarism-icon"
  >
    <!-- 简约现代风格：盾牌 + 对比 -->
    <path
      d="M24 6 L38 12 L38 24 C38 34 24 42 24 42 C24 42 10 34 10 24 L10 12 Z"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linejoin="round"
    />
    <!-- 中间分割线 -->
    <line x1="24" y1="14" x2="24" y2="38" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
    <!-- 左侧对勾 -->
    <polyline
      points="18,26 20,28 24,24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <!-- 右侧叉 -->
    <line x1="27" y1="23" x2="31" y2="27" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
    <line x1="31" y1="23" x2="27" y2="27" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
  </svg>
</template>

<script setup>
</script>

<style scoped>
.plagiarism-icon {
  display: inline-block;
}
</style>
