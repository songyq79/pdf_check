import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'

// ── 基础配置 ──────────────────────────────────────────────────────────
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 不同请求类型的超时（毫秒）
const TIMEOUTS = {
  upload: 120_000,   // 文件上传：2分钟
  poll:    8_000,    // 状态轮询：8秒
  default: 30_000,   // 普通请求：30秒
}

// 选择超时
function getTimeout(config) {
  if (config.timeout) return config.timeout
  const url = config.url || ''
  if (url.includes('/upload') || url.includes('/format')) return TIMEOUTS.upload
  if (url.includes('/status/') || url.includes('/health')) return TIMEOUTS.poll
  return TIMEOUTS.default
}

// ── 创建实例 ──────────────────────────────────────────────────────────
const request = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// ── 重试逻辑 ──────────────────────────────────────────────────────────
const MAX_RETRIES = 2          // 最多重试2次（共3次请求）
const RETRY_DELAY_MS = 1000   // 首次重试等待1秒，之后翻倍

function shouldRetry(error) {
  // 4xx 客户端错误不重试
  if (error.response && error.response.status < 500) return false
  // 网络超时/无响应/5xx 可重试
  return true
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// ── 请求拦截器 ────────────────────────────────────────────────────────
request.interceptors.request.use(
  (config) => {
    config.timeout = getTimeout(config)
    config._retryCount = config._retryCount || 0
    // 自动附加 token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('[request] 请求配置错误:', error)
    return Promise.reject(error)
  }
)

// ── 响应拦截器 ────────────────────────────────────────────────────────
request.interceptors.response.use(
  (response) => response.data,

  async (error) => {
    const config = error.config

    // 402: 额度不足，弹窗提示并可选跳转
    if (error.response?.status === 402) {
      ElMessageBox.confirm(
        '本次操作失败，您的可用次数已不足，可前往购买',
        '次数不足',
        {
          confirmButtonText: '去购买',
          cancelButtonText: '暂不购买',
          confirmButtonClass: 'el-button--primary',
          customStyle: { '--el-color-primary': 'rgb(0, 108, 73)' },
          showClose: false,
        }
      ).then(() => {
        router.push('/pricing')
      }).catch(() => {})
      return Promise.reject(error)
    }

    // 自动重试
    if (config && shouldRetry(error) && config._retryCount < MAX_RETRIES) {
      config._retryCount += 1
      const delay = RETRY_DELAY_MS * config._retryCount
      console.warn(
        `[request] 请求失败，${delay}ms 后第 ${config._retryCount} 次重试:`,
        config.url
      )
      await sleep(delay)
      return request(config)
    }

    // 格式化错误信息
    const message = formatErrorMessage(error)

    // 轮询请求（/status/）静默处理，不弹出提示
    const isPolling = config?.url?.includes('/status/')
    if (!isPolling) {
      ElMessage.error(message)
    }

    console.error('[request] 最终错误:', config?.url, message)
    // 附上友好提示供调用方使用
    error._userMessage = message
    return Promise.reject(error)
  }
)

// ── 错误信息格式化 ────────────────────────────────────────────────────
function formatErrorMessage(error) {
  if (error.response) {
    const { status, data } = error.response
    const detail = data?.detail || data?.message
    switch (status) {
      case 400: return detail || '请求参数错误'
      case 401: return '未授权，请登录'
      case 402: return detail || '配额不足'
      case 403: return '拒绝访问'
      case 404: return detail || '请求的资源不存在'
      case 413: return '文件过大，请压缩后重试'
      case 422: return detail || '请求参数验证失败'
      case 503: return '服务暂时不可用，请稍后重试'
      case 504: return '服务响应超时，请稍后重试'
      case 500: return detail || '服务器内部错误'
      default:  return detail || `请求失败 (${status})`
    }
  }

  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return '请求超时，请检查网络或稍后重试'
  }

  if (error.request) {
    return '无法连接到服务器，请确认后端服务已启动'
  }

  return error.message || '未知错误'
}

export default request
