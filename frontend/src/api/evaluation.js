import request from './index'

/**
 * 评价API
 */
const evaluationAPI = {
  /**
   * 上传文件并进行智能评价
   * @param {FormData} formData - 包含文件的FormData对象
   * @param {Object} config - axios配置（如onUploadProgress）
   * @returns {Promise} - 评价结果
   */
  upload(formData, config = {}) {
    return request({
      url: '/api/v1/evaluation/upload',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      ...config
    })
  },

  downloadReport(reportId) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const a = document.createElement('a')
    a.href = `${baseURL}/api/v1/evaluation/download/${reportId}`
    a.target = '_blank'
    a.click()
  }
}

export default evaluationAPI
