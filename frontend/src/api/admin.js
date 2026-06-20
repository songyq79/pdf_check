/**
 * 管理后台 API
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1/admin`,
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
 * 获取系统配置
 */
export function getSettings() {
  return api.get('/settings')
}

/**
 * 修改系统配置
 * @param {object} updates - 要修改的配置项
 */
export function updateSettings(updates) {
  return api.put('/settings', updates)
}

/**
 * 获取用户列表
 * @param {string} keyword - 搜索关键词
 */
export function listUsers(keyword) {
  return api.get('/users', { params: { keyword } })
}

/**
 * 赠送用户额度
 * @param {number} userId
 * @param {number} count
 */
export function grantQuota(userId, count, source = 'purchase') {
  return api.post(`/users/${userId}/grant-quota`, { count, source })
}

/**
 * 获取订单列表
 * @param {string} status - 筛选状态
 */
export function listOrders(status) {
  return api.get('/orders', { params: { status } })
}

/**
 * 退款（已废弃，请使用 approveRefund）
 * @param {string} orderNo
 */
export function refundOrder(orderNo) {
  return api.post(`/orders/${orderNo}/refund`)
}

/**
 * 获取待审核的退款申请列表
 */
export function listRefundRequests() {
  return api.get('/refund-requests')
}

/**
 * 审核通过退款（支持部分退款）
 * @param {string} orderNo
 * @param {number} refundAmountCents - 退款金额（分），最小1，最大不超过订单金额
 */
export function approveRefund(orderNo, refundAmountCents) {
  return api.post(`/orders/${orderNo}/refund-approve`, { refund_amount_cents: refundAmountCents })
}

/**
 * 审核拒绝退款
 * @param {string} orderNo
 * @param {string} reason - 拒绝原因
 */
export function rejectRefund(orderNo, reason) {
  return api.post(`/orders/${orderNo}/refund-reject`, { reason })
}

/**
 * 创建新用户
 * @param {object} userData - 用户数据 { username, password, email?, is_admin? }
 */
export function createUser(userData) {
  const authApi = axios.create({
    baseURL: `${BASE_URL}/api/v1/auth`,
    timeout: 10000,
  })
  const token = localStorage.getItem('access_token')
  if (token) {
    authApi.defaults.headers.Authorization = `Bearer ${token}`
  }
  return authApi.post('/admin/users', userData)
}

/**
 * 获取所有用户列表
 */
export function getAllUsers() {
  // 用户管理接口在 auth 模块，需要单独调用
  const authApi = axios.create({
    baseURL: `${BASE_URL}/api/v1/auth`,
    timeout: 10000,
  })
  const token = localStorage.getItem('access_token')
  if (token) {
    authApi.defaults.headers.Authorization = `Bearer ${token}`
  }
  return authApi.get('/admin/users')
}

/**
 * 获取近一周活跃用户数（有消耗记录的去重用户）
 */
export function getActiveUsersCount() {
  return api.get('/stats/active-users')
}

// ── 本地论文库 ──────────────────────────────────────────────

export function getPaperStats() {
  return api.get('/local-papers/stats')
}

export function listPapers(params) {
  return api.get('/local-papers', { params })
}

export function getPaperDetail(id) {
  return api.get(`/local-papers/${id}`)
}

export function deletePaper(id) {
  return api.delete(`/local-papers/${id}`)
}

export function rebuildIndex() {
  return api.post('/local-papers/rebuild', {}, { timeout: 300000 })
}

