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
}

export default writingAssistantAPI
