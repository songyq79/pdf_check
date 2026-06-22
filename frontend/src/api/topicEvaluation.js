import request from './index'

const topicEvaluationAPI = {
  /**
   * 提交选题评估任务（表单字段，非文件）
   * @param {Object} fields - {question, description, discipline, degree_level, paper_type}
   * @returns {Promise<{task_id: string}>}
   */
  submit(fields) {
    const formData = new FormData()
    formData.append('question', fields.question || '')
    formData.append('description', fields.description || '')
    formData.append('discipline', fields.discipline || '')
    formData.append('degree_level', fields.degree_level || '')
    formData.append('paper_type', fields.paper_type || 'humanities')
    return request({
      url: '/api/v1/topic-evaluation/upload',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    })
  },

  /**
   * 提交选题推荐任务（生成候选选题）
   * @param {Object} fields - {discipline, paper_type, keywords, degree_level, count}
   */
  recommend(fields) {
    const formData = new FormData()
    formData.append('discipline', fields.discipline || '')
    formData.append('paper_type', fields.paper_type || 'humanities')
    formData.append('keywords', fields.keywords || '')
    formData.append('degree_level', fields.degree_level || '')
    formData.append('count', fields.count || 5)
    return request({
      url: '/api/v1/topic-evaluation/recommend',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    })
  },

  getStatus(taskId) {
    return request({
      url: `/api/v1/topic-evaluation/status/${taskId}`,
      method: 'get',
    })
  },

  getResult(taskId) {
    return request({
      url: `/api/v1/topic-evaluation/result/${taskId}`,
      method: 'get',
    })
  },

  downloadReport(reportId) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const url = `${baseURL}/api/v1/topic-evaluation/download/${reportId}`
    const a = document.createElement('a')
    a.href = url
    a.target = '_blank'
    a.click()
  },
}

export default topicEvaluationAPI
