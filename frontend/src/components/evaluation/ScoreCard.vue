<template>
  <el-card class="dimension-card" shadow="hover">
    <!-- 卡片头部：维度名称和分数 -->
    <div class="dimension-header">
      <div class="dimension-name">
        <el-icon :size="20" style="margin-right: 8px;">
          <component :is="iconComponent" />
        </el-icon>
        {{ dimensionName }}
      </div>
      <div class="dimension-score">{{ score }}分</div>
    </div>

    <!-- 优点 -->
    <div v-if="strengths && strengths.length > 0" class="section">
      <div class="section-title">
        <el-icon class="text-success"><Select /></el-icon>
        <span>优点</span>
      </div>
      <ul class="list">
        <li v-for="(item, index) in strengths" :key="index" class="list-item">
          {{ item }}
        </li>
      </ul>
    </div>

    <!-- 问题 -->
    <div v-if="weaknesses && weaknesses.length > 0" class="section">
      <div class="section-title">
        <el-icon class="text-warning"><WarningFilled /></el-icon>
        <span>问题</span>
      </div>
      <ul class="list">
        <li v-for="(item, index) in weaknesses" :key="index" class="list-item">
          {{ item }}
        </li>
      </ul>
    </div>

    <!-- 改进建议 -->
    <div v-if="suggestions && suggestions.length > 0" class="section">
      <div class="section-title">
        <el-icon class="text-primary"><Promotion /></el-icon>
        <span>改进建议</span>
      </div>
      <ul class="list">
        <li v-for="(item, index) in suggestions" :key="index" class="list-item">
          {{ item }}
        </li>
      </ul>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { Select, WarningFilled, Promotion, Trophy, Star, ChatDotSquare, Link } from '@element-plus/icons-vue'

const props = defineProps({
  // 维度名称
  dimensionName: {
    type: String,
    required: true
  },
  // 分数
  score: {
    type: Number,
    required: true
  },
  // 优点列表
  strengths: {
    type: Array,
    default: () => []
  },
  // 问题列表
  weaknesses: {
    type: Array,
    default: () => []
  },
  // 改进建议列表
  suggestions: {
    type: Array,
    default: () => []
  }
})

// 根据维度名称选择图标
const iconComponent = computed(() => {
  const iconMap = {
    '学术规范性': Trophy,
    '逻辑与创新性': Star,
    '语言质量': ChatDotSquare,
    '文献引用规范性': Link
  }
  return iconMap[props.dimensionName] || Trophy
})
</script>

<style scoped>
.dimension-card {
  height: 100%;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #ebeef5;
}

.dimension-name {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  display: flex;
  align-items: center;
}

.dimension-score {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.section {
  margin-bottom: 20px;
}

.section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.list-item {
  padding: 8px 0 8px 20px;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  position: relative;
}

.list-item::before {
  content: '•';
  position: absolute;
  left: 8px;
  color: #909399;
}
</style>
