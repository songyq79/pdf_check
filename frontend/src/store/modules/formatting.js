import { defineStore } from 'pinia'
import { ref, computed, onUnmounted } from 'vue'
import formattingAPI from '@/api/formatting'
import { useHistoryStore } from './history'

const POLL_INTERVAL_MS = 3000
const MAX_POLL_RETRIES = 3 // 最多重试3次网络错误

export const useFormattingStore = defineStore('formatting', () => {
  const phase = ref('idle')          // idle | processing | completed | failed
  const progress = ref(0)
  const currentFilename = ref('')
  const currentTaskId = ref(null)
  const selectedTemplateId = ref('')
  const selectedTemplateName = ref('')
  const formatResult = ref({ paragraphs: 0, sections: 0, applied: 0, time: 0 })
  const errorMsg = ref('')
  const warning = ref('') // 降级模式警告信息
  const pendingResult = ref(null)  // 来自历史记录的待展示结果

  let pollTimer = null
  let pollRetryCount = 0
  let isPollingActive = false // 防止重复启动轮询

  const isIdle = computed(() => phase.value === 'idle')
  const isProcessing = computed(() => phase.value === 'processing')
  const isCompleted = computed(() => phase.value === 'completed')
  const isFailed = computed(() => phase.value === 'failed')

  const statusText = computed(() => {
    if (progress.value < 20) return '正在上传文件...'
    if (progress.value < 50) return '正在识别文档结构...'
    return '正在应用模板样式，请稍候...'
  })

  function startPolling(taskId) {
    // 防止重复启动轮询
    if (isPollingActive && pollTimer) {
      console.warn('[formatting] 轮询已在运行，跳过重复启动')
      return
    }

    stopPolling()
    isPollingActive = true
    pollRetryCount = 0

    pollTimer = setInterval(async () => {
      // 检查任务ID是否仍然匹配（防止竞态条件）
      if (taskId !== currentTaskId.value) {
        console.warn('[formatting] 任务ID不匹配，停止轮询')
        stopPolling()
        return
      }

      try {
        const res = await formattingAPI.getStatus(taskId)
        pollRetryCount = 0 // 成功后重置重试计数

        if (res.status === 'processing') {
          progress.value = Math.min(85, progress.value + 8)
        } else if (res.status === 'completed') {
          stopPolling()
          const r = res.result || {}
          formatResult.value = {
            paragraphs: r.sections ?? 0,
            sections: r.sections ?? 0,
            applied: r.sections ?? 0,
            time: res.end_time && res.start_time
              ? ((new Date(res.end_time) - new Date(res.start_time)) / 1000).toFixed(1)
              : (r.time_elapsed ?? 0),
          }
          warning.value = res.warning || '' // 保存警告信息
          progress.value = 100
          phase.value = 'completed'
          const historyStore = useHistoryStore()
          historyStore.addRecord({
            type: 'formatting',
            result: {
              file_name: currentFilename.value,
              task_id: currentTaskId.value,
              template_name: selectedTemplateName.value,
              warning: warning.value,
              ...formatResult.value,
            },
            timestamp: Date.now()
          })
        } else if (res.status === 'failed') {
          stopPolling()
          phase.value = 'failed'
          errorMsg.value = res.error || '排版失败'
        }
      } catch (err) {
        pollRetryCount++
        console.warn(`[formatting] 轮询失败 (${pollRetryCount}/${MAX_POLL_RETRIES}):`, err.message)
        
        // 超过最大重试次数，停止轮询并标记失败
        if (pollRetryCount >= MAX_POLL_RETRIES) {
          stopPolling()
          phase.value = 'failed'
          errorMsg.value = '网络连接失败，请检查后重试'
        }
      }
    }, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    isPollingActive = false
    pollRetryCount = 0
  }

  async function uploadAndFormat(file, templateId, templateName) {
    phase.value = 'processing'
    progress.value = 5
    currentFilename.value = file.name
    selectedTemplateId.value = templateId
    selectedTemplateName.value = templateName
    errorMsg.value = ''

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('template_id', templateId)
      const res = await formattingAPI.format(formData)
      currentTaskId.value = res.task_id
      progress.value = 20
      startPolling(res.task_id)
    } catch (err) {
      if (err?.response?.status === 402) {
        phase.value = 'idle'
      } else {
        phase.value = 'failed'
        errorMsg.value = err?.response?.data?.detail || '提交失败，请重试'
      }
      throw err
    }
  }

  function cancel() {
    stopPolling()
    reset()
  }

  function reset() {
    stopPolling()
    phase.value = 'idle'
    progress.value = 0
    currentFilename.value = ''
    currentTaskId.value = null
    formatResult.value = { paragraphs: 0, sections: 0, applied: 0, time: 0 }
    errorMsg.value = ''
    warning.value = ''
  }

  // 切回页面时，若任务仍在 processing 则恢复轮询
  function resumeIfProcessing() {
    if (phase.value === 'processing' && currentTaskId.value && !isPollingActive) {
      startPolling(currentTaskId.value)
    }
  }

  /**
   * 页面挂载时调用：
   * 若有来自历史记录的待展示结果则加载，否则保持当前状态
   */
  function loadPendingOrKeep() {
    if (pendingResult.value) {
      currentFilename.value = pendingResult.value.file_name || ''
      currentTaskId.value = pendingResult.value.task_id || null
      selectedTemplateName.value = pendingResult.value.template_name || ''
      warning.value = pendingResult.value.warning || ''
      formatResult.value = {
        paragraphs: pendingResult.value.paragraphs || 0,
        sections: pendingResult.value.sections || 0,
        applied: pendingResult.value.applied || 0,
        time: pendingResult.value.time || 0,
      }
      progress.value = 100
      phase.value = 'completed'
      pendingResult.value = null
    }
  }

  /** 历史记录页跳转前调用，暂存要展示的结果 */
  function setPendingResult(result) {
    pendingResult.value = result
  }

  // 组件卸载时确保清理定时器
  onUnmounted(() => {
    stopPolling()
  })

  return {
    phase, progress, currentFilename, currentTaskId,
    selectedTemplateId, selectedTemplateName, formatResult, errorMsg, warning, pendingResult,
    isIdle, isProcessing, isCompleted, isFailed, statusText,
    uploadAndFormat, cancel, reset, resumeIfProcessing, stopPolling,
    loadPendingOrKeep, setPendingResult,
  }
})
