/**
 * 论文查重 API
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1/plagiarism`,
  timeout: 120000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})


/**
 * 上传文件，发起查重
 * @param {File} file 上传文件
 * @param {string} paperType 档位(本科/硕士/博士/期刊)
 * @param {string} language auto|zh|en,外文 Tab 传 en
 */
export function uploadAndCheck(file, paperType = '', language = 'auto', content = '') {
  const formData = new FormData()
  if (file) formData.append('file', file)
  if (content) formData.append('content', content)
  if (paperType) formData.append('paper_type', paperType)
  formData.append('language', language)
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 前端启动拉取 feature flag */
export function getConfig() {
  return api.get('/config')
}

/**
 * 查询任务状态
 */
export function getStatus(taskId) {
  return api.get(`/status/${taskId}`)
}

/**
 * 获取查重报告
 */
export function getReport(taskId) {
  return api.get(`/report/${taskId}`)
}
