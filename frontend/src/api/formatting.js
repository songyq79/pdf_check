import request from './index'

const formattingAPI = {
  /**
   * 获取后端可用模板列表
   */
  getTemplates(category = null) {
    return request({
      url: '/api/v1/formatter/templates',
      method: 'get',
      params: category ? { category } : {},
    })
  },

  /**
   * 提交格式化任务
   * @param {FormData} formData - 包含 file 和 template_id 字段
   */
  format(formData) {
    return request({
      url: '/api/v1/formatter/format',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    })
  },

  /**
   * 查询格式化任务状态
   * @param {string} taskId
   */
  getStatus(taskId) {
    return request({
      url: `/api/v1/formatter/status/${taskId}`,
      method: 'get',
    })
  },

  /**
   * 触发浏览器下载格式化结果
   * @param {string} taskId
   */
  download(taskId) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const url = `${baseURL}/api/v1/formatter/download/${taskId}`
    const a = document.createElement('a')
    a.href = url
    a.target = '_blank'
    a.click()
  },
}

export default formattingAPI
