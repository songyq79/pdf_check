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

  /**
   * 解析模板（第一步：上传 → 提取样式配置）
   * @param {FormData} formData - 包含 file, name, description
   */
  analyzeTemplate(formData) {
    return request({
      url: '/api/v1/formatter/templates/analyze',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    })
  },

  /**
   * 确认保存模板（第二步）
   * @param {Object} data - { temp_id, name, description }
   */
  confirmTemplate(data) {
    return request({
      url: '/api/v1/formatter/templates/confirm',
      method: 'post',
      data,
    })
  },

  /**
   * 取消/清理临时模板
   * @param {string} tempId
   */
  cancelTemplate(tempId) {
    return request({
      url: `/api/v1/formatter/templates/temp/${tempId}`,
      method: 'delete',
    })
  },

  /**
   * 删除已保存的自定义模板
   * @param {string} templateId
   */
  deleteTemplate(templateId) {
    return request({
      url: `/api/v1/formatter/templates/${templateId}`,
      method: 'delete',
    })
  },
}

export default formattingAPI
