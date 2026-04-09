<template>
  <div class="bar-chart">
    <v-chart :option="chartOption" :style="{ height: height + 'px' }" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { getBarChartOption } from '@/utils/chartConfig'

const props = defineProps({
  // 维度分数对象
  dimensionScores: {
    type: Object,
    required: true
  },
  // 图表高度
  height: {
    type: Number,
    default: 350
  }
})

// 图表配置
const chartOption = computed(() => getBarChartOption(props.dimensionScores))
</script>

<style scoped>
.bar-chart {
  width: 100%;
}
</style>
