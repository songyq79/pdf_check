<template>
  <div class="loading-spinner">
    <el-icon class="loading-icon" :size="size">
      <Loading />
    </el-icon>
    <div v-if="text" class="loading-text">{{ text }}</div>
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'

defineProps({
  // 图标大小
  size: {
    type: Number,
    default: 50
  },
  // 加载文字
  text: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.loading-icon {
  color: rgb(0, 108, 73);
  animation: rotate 1.5s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-top: 15px;
  color: rgb(107, 114, 128);
  font-size: 14px;
}
</style>
