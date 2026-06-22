import request from './index'

const writingAssistantAPI = {
  /**
   * 逐段写作检查（同步返回，消耗 2 次额度）
   * @param {string} paragraph
   * @param {string} paperType
   */
  check(paragraph, paperType = 'humanities') {
    return request({
      url: '/api/v1/writing-assistant/check',
      method: 'post',
      data: { paragraph, paper_type: paperType },
      timeout: 45000,
    })
  },

  /** 整篇检查：上传 docx，返回 task_id（异步） */
  checkDocument(file, paperType = 'humanities') {
    const form = new FormData()
    form.append('file', file)
    form.append('paper_type', paperType)
    return request({
      url: '/api/v1/writing-assistant/check-document',
      method: 'post',
      data: form,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
  },

  /** 整篇检查进度 */
  documentStatus(taskId) {
    return request({ url: `/api/v1/writing-assistant/document-status/${taskId}`, method: 'get' })
  },

  /** 整篇检查结果 */
  documentResult(taskId) {
    return request({ url: `/api/v1/writing-assistant/document-result/${taskId}`, method: 'get' })
  },
}

export default writingAssistantAPI
