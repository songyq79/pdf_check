import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import evaluationAPI from '@/api/evaluation'
import { useHistoryStore } from './history'

const POLL_INTERVAL_MS = 2000  // 每2秒轮询一次
const POLL_MAX_WAIT_MS = 300000 // 最多等5分钟
const MAX_POLL_RETRIES = 3 // 最多重试3次网络错误

/**
 * 评价状态管理
 * 状态机: idle -> uploading -> processing -> completed | failed
 */
export const useEvaluationStore = defineStore('evaluation', () => {
  const evaluationStatus = ref('idle') // idle | uploading | processing | completed | failed
  const uploadProgress = ref(0)
  const currentResult = ref(null)
  const currentTaskId = ref(null)
  const error = ref(null)
  const warning = ref(null) // 降级模式警告信息
  const pendingResult = ref(null)  // 来自历史记录的待展示结果

  const isIdle = computed(() => evaluationStatus.value === 'idle')
  const isUploading = computed(() => evaluationStatus.value === 'uploading')
  const isProcessing = computed(() => evaluationStatus.value === 'processing')
  const isCompleted = computed(() => evaluationStatus.value === 'completed')
  const isFailed = computed(() => evaluationStatus.value === 'failed')
  const hasResult = computed(() => currentResult.value !== null)

  /**
   * 上传文件并评价（异步任务版）
   */
  async function uploadAndEvaluate(file) {
    try {
      error.value = null
      warning.value = null
      uploadProgress.value = 0
      currentTaskId.value = null
      evaluationStatus.value = 'uploading'

      const formData = new FormData()
      formData.append('file', file)

      // 1. 上传文件，得到 task_id
      const uploadResp = await evaluationAPI.upload(formData, {
        onUploadProgress: (e) => {
          uploadProgress.value = Math.round((e.loaded * 100) / e.total)
        }
      })

      const taskId = uploadResp.task_id
      currentTaskId.value = taskId
      
      // 保存警告信息（如果有）
      if (uploadResp.warning) {
        warning.value = uploadResp.warning
      }
      
      evaluationStatus.value = 'processing'
      // 确保上传完成后进度不低于10%
      uploadProgress.value = Math.max(uploadProgress.value, 10)

      // 2. 启动轮询
      startPolling(taskId)
    } catch (err) {
      error.value = err.message || '评价失败'
      evaluationStatus.value = 'failed'
      throw err
    }
  }

  function reset() {
    evaluationStatus.value = 'idle'
    uploadProgress.value = 0
    currentResult.value = null
    currentTaskId.value = null
    error.value = null
    warning.value = null
  }

  /**
   * 页面挂载时调用：
   * 若有来自历史记录的待展示结果则加载，否则重置为空闲状态
   */
  function loadPendingOrReset() {
    if (pendingResult.value) {
      currentResult.value = pendingResult.value
      evaluationStatus.value = 'completed'
      pendingResult.value = null
    } else {
      reset()
    }
  }

  /** 历史记录页跳转前调用，暂存要展示的结果 */
  function setPendingResult(result) {
    pendingResult.value = result
  }

  /** 页面挂载时调用：若有待展示结果则加载，否则保持当前状态 */
  function loadPendingOrKeep() {
    if (pendingResult.value) {
      currentResult.value = pendingResult.value
      evaluationStatus.value = 'completed'
      pendingResult.value = null
    }
    // 否则保持当前状态（可能是processing或completed）
  }

  /** 轮询控制 */
  let pollTimer = null
  let pollRetryCount = 0
  let isPollingActive = false

  /**
   * 启动轮询
   */
  function startPolling(taskId) {
    // 防止重复启动轮询
    if (isPollingActive && pollTimer) {
      console.warn('[evaluation] 轮询已在运行，跳过重复启动')
      return
    }

    stopPolling()
    isPollingActive = true
    pollRetryCount = 0

    pollTimer = setInterval(async () => {
      // 检查任务ID是否仍然匹配
      if (taskId !== currentTaskId.value) {
        console.warn('[evaluation] 任务ID不匹配，停止轮询')
        stopPolling()
        return
      }

      try {
        const statusResp = await evaluationAPI.getStatus(taskId)
        pollRetryCount = 0 // 成功后重置重试计数

        const { status, progress } = statusResp

        if (status === 'processing') {
          // 用后端进度更新uploadProgress，只增不减
          if (progress != null && progress > uploadProgress.value) {
            uploadProgress.value = progress
          }
        } else if (status === 'completed') {
          stopPolling()
          // 拉取完整结果
          const result = await evaluationAPI.getResult(taskId)
          currentResult.value = result
          evaluationStatus.value = 'completed'
          uploadProgress.value = 100

          // 存入历史
          const historyStore = useHistoryStore()
          historyStore.addRecord({
            type: 'evaluation',
            result: { ...result, file_name: currentResult.value.paper_title || '未命名论文' },
            timestamp: Date.now()
          })
        } else if (status === 'failed') {
          stopPolling()
          error.value = statusResp.error || '评价任务失败'
          evaluationStatus.value = 'failed'
        }
      } catch (err) {
        pollRetryCount++
        console.warn(`[evaluation] 轮询失败 (${pollRetryCount}/${MAX_POLL_RETRIES}):`, err.message)
        
        // 超过最大重试次数，停止轮询并标记失败
        if (pollRetryCount >= MAX_POLL_RETRIES) {
          stopPolling()
          error.value = '网络连接失败，请检查后重试'
          evaluationStatus.value = 'failed'
        }
      }
    }, POLL_INTERVAL_MS)
  }

  /** 停止轮询 */
  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    isPollingActive = false
    pollRetryCount = 0
  }

  /** 恢复轮询（如果正在处理中） */
  function resumeIfProcessing() {
    if (isProcessing.value && currentTaskId.value && !isPollingActive) {
      startPolling(currentTaskId.value)
    }
  }

  /** 取消评价 */
  function cancel() {
    stopPolling()
    evaluationStatus.value = 'idle'
    uploadProgress.value = 0
    currentTaskId.value = null
    error.value = null
  }

  return {
    evaluationStatus,
    uploadProgress,
    currentResult,
    currentTaskId,
    error,
    warning,
    isIdle,
    isUploading,
    isProcessing,
    isCompleted,
    isFailed,
    hasResult,
    uploadAndEvaluate,
    reset,
    loadPendingOrReset,
    loadPendingOrKeep,
    resumeIfProcessing,
    stopPolling,
    cancel,
    setPendingResult
  }
})
