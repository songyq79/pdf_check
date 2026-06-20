<template>
  <svg
    viewBox="0 0 48 48"
    width="1em"
    height="1em"
    fill="currentColor"
    class="spellcheck-icon"
  >
    <!-- 简约现代风格：文档 + 对勾 -->
    <rect
      x="10"
      y="6"
      width="24"
      height="32"
      rx="2"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
    />
    <!-- 横线 -->
    <line x1="14" y1="14" x2="34" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
    <line x1="14" y1="22" x2="34" y2="22" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
    <line x1="14" y1="30" x2="26" y2="30" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
    <!-- 对勾 -->
    <polyline
      points="28,26 32,32 38,20"
      fill="none"
      stroke="currentColor"
      stroke-width="2.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script setup>
</script>

<style scoped>
.spellcheck-icon {
  display: inline-block;
}
</style>
