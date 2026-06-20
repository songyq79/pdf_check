import request from './index'

const experimentEvaluationAPI = {
  submit(fields) {
    const formData = new FormData()
    formData.append('plan_text', fields.plan_text || '')
    formData.append('discipline', fields.discipline || '')
    return request({
      url: '/api/v1/experiment-evaluation/upload',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    })
  },
  getStatus(taskId) {
    return request({ url: `/api/v1/experiment-evaluation/status/${taskId}`, method: 'get' })
  },
  getResult(taskId) {
    return request({ url: `/api/v1/experiment-evaluation/result/${taskId}`, method: 'get' })
  },
  downloadReport(reportId) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const a = document.createElement('a')
    a.href = `${baseURL}/api/v1/experiment-evaluation/download/${reportId}`
    a.target = '_blank'
    a.click()
  },
}

export default experimentEvaluationAPI
