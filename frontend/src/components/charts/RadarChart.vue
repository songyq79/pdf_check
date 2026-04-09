<template>
  <div class="radar-chart">
    <v-chart :option="chartOption" :style="{ height: height + 'px' }" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { getRadarChartOption } from '@/utils/chartConfig'

const props = defineProps({
  // 维度分数对象 { "学术规范性": 85, "逻辑与创新性": 78, ... }
  dimensionScores: {
    type: Object,
    required: true
  },
  // 图表高度
  height: {
    type: Number,
    default: 400
  }
})

// 图表配置
const chartOption = computed(() => getRadarChartOption(props.dimensionScores))
</script>

<style scoped>
.radar-chart {
  width: 100%;
}
</style>
