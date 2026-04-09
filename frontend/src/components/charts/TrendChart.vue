<template>
  <div class="trend-chart">
    <v-chart :option="chartOption" :style="{ height: height + 'px' }" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { getTrendChartOption } from '@/utils/chartConfig'

const props = defineProps({
  // 历史数据数组 [{ date: '2026-02-11', score: 85 }, ...]
  historyData: {
    type: Array,
    required: true
  },
  // 图表高度
  height: {
    type: Number,
    default: 300
  }
})

// 图表配置
const chartOption = computed(() => getTrendChartOption(props.historyData))
</script>

<style scoped>
.trend-chart {
  width: 100%;
}
</style>
