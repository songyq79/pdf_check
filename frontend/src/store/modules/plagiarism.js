/**
 * 查重模块状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { uploadAndCheck, getStatus, getReport, getConfig } from '@/api/plagiarism'
import { useHistoryStore } from '@/store/modules/history'

export const usePlagiarismStore = defineStore('plagiarism', () => {
  const taskId = ref('')
  const status = ref('idle')
  const progress = ref(0)
  const stage = ref('')            // 当前阶段文字,外文路径 8 个阶段
  const report = ref(null)
  const isFinal = ref(false)
  const errorMsg = ref('')
  const fileName = ref('')
  const pendingResult = ref(null)

  // 双 Tab + 语言 + 计费元信息
  const activeTab = ref('zh')      // zh | en
  const selectedLanguage = ref('auto')
  const detectedLanguage = ref(null)
  const quotaCost = ref(1)
  const englishCheckEnabled = ref(true)

  let pollTimer = null

  async function loadConfig() {
    try {
      const res = await getConfig()
      englishCheckEnabled.value = !!res.data.english_check_enabled
    } catch (e) {
      console.warn('[plagiarism] 读取 config 失败,默认启用外文查重:', e)
      englishCheckEnabled.value = true
    }
  }

  function setActiveTab(tab) {
    if (activeTab.value === tab) return
    activeTab.value = tab
    reset()
  }

  /**
   * 上传并开始查重
   * language: auto | zh | en
   */
  async function startCheck(file, paperType, language = 'auto') {
    reset()
    fileName.value = file.name
    status.value = 'uploading'
    selectedLanguage.value = language

    try {
      const res = await uploadAndCheck(file, paperType, language)
      taskId.value = res.data.task_id
      detectedLanguage.value = res.data.language || null
      quotaCost.value = res.data.quota_cost || 1
      status.value = 'pending'
      progress.value = 5
      startPolling()
    } catch (err) {
      if (err.response?.status === 402) {
        // 额度不足：回到初始状态，弹窗已由拦截器处理
        status.value = 'idle'
      } else {
        errorMsg.value = err.message || '上传失败'
        status.value = 'failed'
      }
      throw err
    }
  }

  /**
   * 轮询任务状态
   */
  function startPolling() {
    pollTimer = setInterval(async () => {
      try {
        const res = await getStatus(taskId.value)
        const data = res.data
        progress.value = data.progress || progress.value
        stage.value = data.stage || stage.value
        status.value = data.status

        if (data.status === 'partial' || data.status === 'done') {
          const reportRes = await getReport(taskId.value)
          report.value = reportRes.data
          isFinal.value = data.status === 'done'

          if (data.status === 'done') {
            stopPolling()
            saveToHistory()
          }
        } else if (data.status === 'failed') {
          errorMsg.value = data.error || '检测失败，请重试'
          stopPolling()
        }
      } catch (e) {
        console.error('[plagiarism] 轮询失败:', e)
      }
    }, 2000)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  /**
   * 保存到历史记录
   */
  function saveToHistory() {
    if (!report.value) return
    const historyStore = useHistoryStore()
    historyStore.addRecord({
      type: 'plagiarism',
      timestamp: Date.now(),
      result: {
        file_name: fileName.value,
        rate: report.value.summary?.rate ?? 0,
        risk_level: report.value.summary?.risk_level ?? 'low',
        engine: report.value.engine ?? '',
        task_id: taskId.value,
        // 完整报告存入，供历史记录查看详情
        full_report: report.value,
      }
    })
  }

  /**
   * 从历史记录恢复
   */
  function setPendingResult(result) {
    pendingResult.value = result
  }

  function reset() {
    stopPolling()
    taskId.value = ''
    status.value = 'idle'
    progress.value = 0
    stage.value = ''
    report.value = null
    isFinal.value = false
    errorMsg.value = ''
    fileName.value = ''
    pendingResult.value = null
    detectedLanguage.value = null
    quotaCost.value = 1
  }

  return {
    taskId, status, progress, stage, report, isFinal, errorMsg, fileName, pendingResult,
    activeTab, selectedLanguage, detectedLanguage, quotaCost, englishCheckEnabled,
    startCheck, reset, setPendingResult, stopPolling, setActiveTab, loadConfig,
  }
})
