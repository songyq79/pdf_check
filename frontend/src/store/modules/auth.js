/**
 * 用户认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getMe } from '@/api/auth'
import { useBillingStore } from './billing'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const user = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')
  const isAdmin = computed(() => user.value?.is_admin || false)
  const isApproved = computed(() => user.value?.is_approved || false)

  /**
   * 登录：保存 token，拉取用户信息
   */
  async function loginAction(username, password) {
    const res = await apiLogin(username, password)
    token.value = res.data.access_token
    localStorage.setItem('access_token', token.value)
    await fetchMe()
  }

  /**
   * 通过 token 直接登录（用于第三方登录和短信验证码登录）
   */
  async function loginWithToken(accessToken) {
    token.value = accessToken
    localStorage.setItem('access_token', accessToken)
    await fetchMe()
  }

  /**
   * 拉取当前用户信息
   */
  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await getMe()
      user.value = res.data

      // 检查用户是否被拒绝（is_active = false）
      if (!user.value.is_active) {
        logout()
        return
      }

      // 加载计费数据
      const billingStore = useBillingStore()
      await Promise.all([
        billingStore.loadPricing(),
        billingStore.loadQuota(),
      ])
    } catch {
      // token 失效则退出
      logout()
    }
  }

  /**
   * 退出登录
   */
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
  }

  return { token, user, isLoggedIn, username, isAdmin, isApproved, loginAction, loginWithToken, fetchMe, logout }
})
