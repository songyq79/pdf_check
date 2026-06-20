import request from './index'

const literatureReviewAPI = {
  /**
   * 提交文献综述任务（文件或关键词二选一）
   * @param {Object} fields - {file?: File, keywords, topic, discipline, paper_type, citation_style}
   */
  submit(fields) {
    const formData = new FormData()
    if (fields.file) formData.append('file', fields.file)
    formData.append('keywords', fields.keywords || '')
    formData.append('topic', fields.topic || '')
    formData.append('discipline', fields.discipline || '')
    formData.append('paper_type', fields.paper_type || 'humanities')
    formData.append('citation_style', fields.citation_style || 'gbt7714')
    return request({
      url: '/api/v1/literature-review/upload',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
  },

  getStatus(taskId) {
    return request({ url: `/api/v1/literature-review/status/${taskId}`, method: 'get' })
  },

  getResult(taskId) {
    return request({ url: `/api/v1/literature-review/result/${taskId}`, method: 'get' })
  },

  downloadReport(reportId) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const url = `${baseURL}/api/v1/literature-review/download/${reportId}`
    const a = document.createElement('a')
    a.href = url
    a.target = '_blank'
    a.click()
  },
}

export default literatureReviewAPI
