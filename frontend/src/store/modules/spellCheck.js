import { defineStore } from 'pinia'
import { ref, computed, onUnmounted } from 'vue'
import spellCheckAPI from '@/api/spellCheck'
import { useHistoryStore } from './history'

const POLL_INTERVAL_MS = 3000
const MAX_POLL_RETRIES = 3 // 最多重试3次网络错误

export const useSpellCheckStore = defineStore('spellCheck', () => {
  const phase = ref('idle')          // idle | processing | completed | failed
  const progress = ref(0)
  const currentFilename = ref('')
  const currentTaskId = ref(null)
  const stats = ref({ total: 0, changed: 0, skipped: 0 })
  const finishedAt = ref(null)
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
    if (progress.value < 10) return '正在上传文件...'
    if (progress.value < 50) return '正在初始化校对任务...'
    return 'AI 逐段校对中，请稍候（视文档长度约需 1-3 分钟）...'
  })

  function startPolling(taskId) {
    // 防止重复启动轮询
    if (isPollingActive && pollTimer) {
      console.warn('[spellCheck] 轮询已在运行，跳过重复启动')
      return
    }

    stopPolling()
    isPollingActive = true
    pollRetryCount = 0

    pollTimer = setInterval(async () => {
      // 检查任务ID是否仍然匹配（防止竞态条件）
      if (taskId !== currentTaskId.value) {
        console.warn('[spellCheck] 任务ID不匹配，停止轮询')
        stopPolling()
        return
      }

      try {
        const res = await spellCheckAPI.getStatus(taskId)
        pollRetryCount = 0 // 成功后重置重试计数

        if (res.status === 'processing') {
          progress.value = Math.min(90, progress.value + 5)
        } else if (res.status === 'completed') {
          stopPolling()
          stats.value = res.stats || { total: 0, changed: 0, skipped: 0 }
          finishedAt.value = res.finished_at
          warning.value = res.warning || '' // 保存警告信息
          progress.value = 100
          phase.value = 'completed'
          const historyStore = useHistoryStore()
          historyStore.addRecord({
            type: 'spellcheck',
            result: {
              file_name: currentFilename.value,
              task_id: currentTaskId.value,
              stats: stats.value,
              finished_at: res.finished_at,
              warning: warning.value,
            },
            timestamp: Date.now()
          })
        } else if (res.status === 'failed') {
          stopPolling()
          phase.value = 'failed'
          errorMsg.value = res.error || '校对失败'
        }
      } catch (err) {
        pollRetryCount++
        console.warn(`[spellCheck] 轮询失败 (${pollRetryCount}/${MAX_POLL_RETRIES}):`, err.message)
        
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

  async function uploadAndCheck(file) {
    phase.value = 'processing'
    progress.value = 5
    currentFilename.value = file.name
    errorMsg.value = ''

    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await spellCheckAPI.upload(formData)
      currentTaskId.value = res.task_id
      progress.value = 15
      startPolling(res.task_id)
    } catch (err) {
      phase.value = 'failed'
      errorMsg.value = err?.response?.data?.detail || '上传失败，请重试'
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
    stats.value = { total: 0, changed: 0, skipped: 0 }
    finishedAt.value = null
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
      stats.value = pendingResult.value.stats || { total: 0, changed: 0, skipped: 0 }
      finishedAt.value = pendingResult.value.finished_at || null
      warning.value = pendingResult.value.warning || ''
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
    stats, finishedAt, errorMsg, warning, pendingResult,
    isIdle, isProcessing, isCompleted, isFailed, statusText,
    uploadAndCheck, cancel, reset, resumeIfProcessing, stopPolling,
    loadPendingOrKeep, setPendingResult,
  }
})
