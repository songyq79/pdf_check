import request from './index'

const evaluationAPI = {
  /**
   * 上传文件并触发评价任务
   * @param {FormData} formData - 包含 file 字段
   * @param {Object} config - axios 配置（如 onUploadProgress）
   * @returns {Promise<{task_id: string}>}
   */
  upload(formData, config = {}) {
    return request({
      url: '/api/v1/evaluation/upload',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // 2分钟
      ...config,
    })
  },

  /**
   * 查询评价任务状态
   * @param {string} taskId
   * @returns {Promise<{status: string, progress?: number, error?: string}>}
   */
  getStatus(taskId) {
    return request({
      url: `/api/v1/evaluation/status/${taskId}`,
      method: 'get',
    })
  },

  /**
   * 获取评价结果
   * @param {string} taskId
   * @returns {Promise<Object>} 评价结果对象
   */
  getResult(taskId) {
    return request({
      url: `/api/v1/evaluation/result/${taskId}`,
      method: 'get',
    })
  },

  /**
   * 基于评价结果获取期刊投稿推荐（免费）
   * @param {string} taskId
   */
  getJournalRecommendations(taskId) {
    return request({
      url: `/api/v1/evaluation/journal-recommendations/${taskId}`,
      method: 'get',
    })
  },

  /**
   * 按论文内容选刊（贴标题/摘要/关键词，免费）
   * @param {Object} fields - {title, abstract, keywords, paper_type}
   */
  journalSelect(fields) {
    const form = new FormData()
    form.append('title', fields.title || '')
    form.append('abstract', fields.abstract || '')
    form.append('keywords', fields.keywords || '')
    form.append('paper_type', fields.paper_type || '')
    return request({
      url: '/api/v1/evaluation/journal-select',
      method: 'post',
      data: form,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    })
  },

  /**
   * 按刊名取维普期刊详情（含后端缓存）
   * @param {string} name 刊名
   */
  journalDetailByName(name) {
    const form = new FormData()
    form.append('name', name)
    return request({
      url: '/api/v1/evaluation/journal-detail-by-name',
      method: 'post',
      data: form,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    })
  },

  /**
   * 下载评价报告
   * @param {string} reportId
   */
  downloadReport(reportId) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const url = `${baseURL}/api/v1/evaluation/download/${reportId}`
    const a = document.createElement('a')
    a.href = url
    a.target = '_blank'
    a.click()
  },
}

export default evaluationAPI
