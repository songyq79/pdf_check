<template>
  <svg
    viewBox="0 0 48 48"
    width="1em"
    height="1em"
    fill="currentColor"
    class="formatting-icon"
  >
    <!-- 简约现代风格：文档排版 -->
    <rect
      x="10"
      y="6"
      width="28"
      height="36"
      rx="2"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
    />
    <!-- 标题行 -->
    <line x1="14" y1="14" x2="34" y2="14" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
    <!-- 内容行 -->
    <line x1="14" y1="22" x2="34" y2="22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
    <line x1="14" y1="27" x2="34" y2="27" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
    <line x1="14" y1="32" x2="28" y2="32" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
  </svg>
</template>

<script setup>
</script>

<style scoped>
.formatting-icon {
  display: inline-block;
}
</style>
