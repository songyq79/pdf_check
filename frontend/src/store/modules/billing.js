/**
 * 计费 Store Module
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as billingApi from '@/api/billing'

export const useBillingStore = defineStore('billing', () => {
  // 状态
  const pricing = ref(null)
  const quota = ref(null)
  const orders = ref([])
  const inviteCodes = ref([])
  const usageHistory = ref([])

  // 计算属性
  const billingEnabled = computed(() => pricing.value?.billing_enabled || false)
  const hasAccess = computed(() => quota.value?.has_access || false)
  const totalCredits = computed(() => quota.value?.total_credits || 0)
  const subscription = computed(() => quota.value?.subscription)

  // 加载定价
  const loadPricing = async () => {
    try {
      const res = await billingApi.getPricing()
      pricing.value = res.data
    } catch (e) {
      console.error('加载定价失败:', e)
    }
  }

  // 加载我的配额
  const loadQuota = async () => {
    try {
      const res = await billingApi.getMyQuota()
      quota.value = res.data
    } catch (e) {
      console.error('加载配额失败:', e)
    }
  }

  // 加载订单列表
  const loadOrders = async () => {
    try {
      const res = await billingApi.getMyOrders()
      orders.value = res.data || []
    } catch (e) {
      console.error('加载订单失败:', e)
    }
  }

  // 创建订单
  const createOrder = async (productType, payMethod, quantity = 1) => {
    try {
      const res = await billingApi.createOrder(productType, payMethod, quantity)
      return res.data
    } catch (e) {
      console.error('创建订单失败:', e)
      throw e
    }
  }

  // 加载邀请码
  const loadInviteCodes = async () => {
    try {
      const res = await billingApi.getMyInviteCodes()
      inviteCodes.value = res.data || []
    } catch (e) {
      console.error('加载邀请码失败:', e)
    }
  }

  // 生成邀请码
  const genInviteCode = async () => {
    try {
      const res = await billingApi.generateInviteCode()
      await loadInviteCodes()
      return res.data.code
    } catch (e) {
      console.error('生成邀请码失败:', e)
      throw e
    }
  }

  // 加载使用记录
  const loadUsageHistory = async () => {
    try {
      const res = await billingApi.getUsageHistory()
      usageHistory.value = res.data || []
    } catch (e) {
      console.error('加载使用记录失败:', e)
    }
  }

  return {
    // 状态
    pricing,
    quota,
    orders,
    inviteCodes,
    usageHistory,
    // 计算属性
    billingEnabled,
    hasAccess,
    totalCredits,
    subscription,
    // 方法
    loadPricing,
    loadQuota,
    loadOrders,
    createOrder,
    loadInviteCodes,
    genInviteCode,
    loadUsageHistory,
  }
})
