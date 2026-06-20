/**
 * 认证相关 API
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1/auth`,
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
 * 登录
 * @param {string} username
 * @param {string} password
 */
export function login(username, password) {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  return api.post('/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}

/**
 * 注册
 * @param {string} username
 * @param {string} password
 * @param {string} email
 */
export function register(username, password, email) {
  return api.post('/register', { username, password, email })
}

/**
 * 获取当前用户信息
 */
export function getMe() {
  return api.get('/me')
}

/**
 * 发送短信验证码
 * @param {string} phone
 */
export function sendSmsCode(phone) {
  return api.post('/sms/send', { phone })
}

/**
 * 手机号验证码登录/注册
 * @param {string} phone
 * @param {string} code
 * @param {string} inviteCode
 */
export function smsLogin(phone, code, inviteCode) {
  return api.post('/sms/login', { phone, code, invite_code: inviteCode })
}

/**
 * 获取微信登录URL
 */
export function getWechatLoginUrl() {
  return api.get('/wechat/url')
}

/**
 * 获取支付宝登录URL
 */
export function getAlipayLoginUrl() {
  return api.get('/alipay/url')
}
