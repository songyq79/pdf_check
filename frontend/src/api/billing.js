/**
 * 计费相关 API
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1/billing`,
  timeout: 10000,
})

// 请求拦截器：自动带上 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * 获取定价信息（公开）
 */
export function getPricing() {
  return api.get('/pricing')
}

/**
 * 获取各功能消耗的 credit 对照表（公开）
 */
export function getFeatureCosts() {
  return api.get('/feature-costs')
}

/**
 * 获取我的配额
 */
export function getMyQuota() {
  return api.get('/quota')
}

/**
 * 创建订单
 * @param {string} productType - per_use 或 monthly
 * @param {string} payMethod - wechat 或 alipay
 * @param {number} quantity - 购买数量（仅 per_use 时有效）
 */
export function createOrder(productType, payMethod, quantity = 1) {
  return api.post('/orders', {
    product_type: productType,
    pay_method: payMethod,
    quantity,
  })
}

/**
 * 获取我的订单列表
 */
export function getMyOrders() {
  return api.get('/orders')
}

/**
 * 查询订单支付状态
 * @param {string} orderNo
 */
export function getOrderStatus(orderNo) {
  return api.get(`/orders/${orderNo}/status`)
}

/**
 * 获取使用记录
 */
export function getUsageHistory() {
  return api.get('/usage')
}

/**
 * 生成邀请码
 */
export function generateInviteCode() {
  return api.post('/invite/generate')
}

/**
 * 获取我的邀请码列表
 */
export function getMyInviteCodes() {
  return api.get('/invite/my-codes')
}

/**
 * 申请退款
 * @param {string} orderNo - 订单号
 * @param {string} reason - 退款原因
 */
export function applyRefund(orderNo, reason) {
  return api.post(`/orders/${orderNo}/refund-request`, { reason })
}
