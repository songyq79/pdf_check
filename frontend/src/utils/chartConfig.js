/**
 * ECharts图表配置工具
 */

/**
 * 获取雷达图配置
 * @param {Object} dimensionScores - 维度分数对象 { "学术规范性": 85, ... }
 * @returns {Object} - ECharts配置对象
 */
export function getRadarChartOption(dimensionScores = {}) {
  const dimensions = ['选题意义', '写作安排', '逻辑构建', '专业能力', '学术规范']
  const values = dimensions.map(dim => dimensionScores[dim] || 0)

  return {
    title: {
      text: '论文评价雷达图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: dimensions.map(name => ({
        name,
        max: 100
      })),
      radius: '65%',
      axisName: {
        color: '#666',
        fontSize: 12
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(0, 108, 73, 0.06)', 'rgba(0, 108, 73, 0.12)']
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '评分',
        areaStyle: {
          color: 'rgba(0, 108, 73, 0.2)'
        },
        lineStyle: {
          color: '#006C49',
          width: 2
        },
        itemStyle: {
          color: '#006C49'
        }
      }]
    }]
  }
}

/**
 * 获取柱状图配置
 * @param {Object} dimensionScores - 维度分数对象
 * @returns {Object} - ECharts配置对象
 */
export function getBarChartOption(dimensionScores = {}) {
  const dimensions = Object.keys(dimensionScores)
  const values = Object.values(dimensionScores)

  return {
    title: {
      text: '各维度得分对比',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: dimensions,
      axisLabel: {
        interval: 0,
        rotate: dimensions.length > 4 ? 30 : 0
      }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}分'
      }
    },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: {
        color: '#006C49'
      },
      label: {
        show: true,
        position: 'top',
        formatter: '{c}分'
      }
    }]
  }
}

/**
 * 获取趋势图配置
 * @param {Array} historyData - 历史数据数组 [{ date, score }, ...]
 * @returns {Object} - ECharts配置对象
 */
export function getTrendChartOption(historyData = []) {
  const dates = historyData.map(item => item.date)
  const scores = historyData.map(item => item.score)

  return {
    title: {
      text: '评分趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}分'
      }
    },
    series: [{
      type: 'line',
      data: scores,
      smooth: true,
      itemStyle: {
        color: '#006C49'
      },
      areaStyle: {
        color: 'rgba(0, 108, 73, 0.12)'
      }
    }]
  }
}

/**
 * 通用图表响应式配置
 */
export const chartResponsiveConfig = {
  maintainAspectRatio: false,
  responsive: true
}
