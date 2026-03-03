import request from './index'

const spellCheckAPI = {
  /**
   * 上传文件，触发后台校对任务
   * @returns {Promise<{task_id, status_url, download_url}>}
   */
  upload(formData) {
    return request({
      url: '/api/v1/proofread/upload',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    })
  },

  /**
   * 查询任务状态
   * @param {string} taskId
   * @returns {Promise<{status, progress, stats, download_url}>}
   */
  getStatus(taskId) {
    return request({
      url: `/api/v1/proofread/status/${taskId}`,
      method: 'get',
    })
  },

  /**
   * 触发浏览器下载校对结果文件
   * @param {string} taskId
   */
  download(taskId) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const url = `${baseURL}/api/v1/proofread/download/${taskId}`
    const a = document.createElement('a')
    a.href = url
    a.target = '_blank'
    a.click()
  },
}

export default spellCheckAPI
