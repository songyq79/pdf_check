<template>
  <div class="pricing-page">
    <div class="pricing-header">
      <h1>选择适合你的套餐</h1>
      <p>开启无限可能的学术之旅</p>
    </div>

    <!-- 计费口径说明 -->
    <div class="billing-note">
      计费以 <strong>credit（次）</strong> 为单位：<strong>¥{{ pricePerUse }}/credit</strong>。
      不同功能消耗的 credit 数不同，详见下表。
    </div>

    <div class="pricing-container">
      <!-- 按次购买 -->
      <div class="pricing-card pay-per-use">
        <div class="card-title">
          <h3>按次购买</h3>
          <p class="price">
            <span class="currency">¥</span><span class="amount">{{ pricePerUse }}</span><span class="unit">/credit</span>
          </p>
        </div>
        <div class="card-content">
          <p class="desc">随用随买，灵活使用</p>
          <div class="features">
            <div class="feature">✓ 全部功能可用</div>
            <div class="feature">✓ 按功能消耗 credit（见下表）</div>
            <div class="feature">✓ 无过期限制</div>
          </div>
          <el-input-number v-model="perUseQuantity" :min="1" :max="100" :precision="0" :step="1" :value-on-clear="1" style="width: 100%; margin-bottom: 15px;">
          </el-input-number>
          <el-button size="large" style="width: 100%; background: rgb(226, 226, 226); color: rgb(26, 28, 28); border: none; border-radius: 9999px; font-size: 16px;" @click="buyPerUse" :loading="buyLoading">
            购买 {{ perUseQuantity }} 次 (¥{{ perUsePrice }})
          </el-button>
        </div>
      </div>

      <!-- 包月 -->
      <div class="pricing-card monthly" :class="{ recommended: true }">
        <div class="ribbon">推荐</div>
        <div class="card-title">
          <h3>包月订阅</h3>
          <p class="price">
            <span class="currency">¥</span><span class="amount">{{ priceMonthly }}</span><span class="unit">/月</span>
          </p>
        </div>
        <div class="card-content">
          <p class="desc">每月 {{ monthlyLimit }} credits 额度</p>
          <div class="features">
            <div class="feature">✓ 每月 {{ monthlyLimit }} credits 额度</div>
            <div class="feature">✓ 优先客服支持</div>
            <div class="feature">✓ 30天有效期</div>
            <div class="feature">✓ 支持续费累计</div>
          </div>
          <el-button size="large" style="width: 100%; background: white; color: rgb(0, 108, 73); border: none; border-radius: 9999px; font-size: 16px;"
            @click="buyMonthly" :loading="buyLoading">
            立即订阅
          </el-button>
        </div>
      </div>
    </div>

    <!-- 各功能消耗对照表 -->
    <div class="cost-table-section">
      <h2>各功能消耗对照</h2>
      <p class="cost-table-sub">每次使用扣除对应 credit；包月套餐同样按此消耗每月额度。</p>
      <div class="cost-table">
        <div class="cost-row cost-head">
          <span class="c-name">功能</span>
          <span class="c-credits">消耗</span>
          <span class="c-yuan">按次价</span>
        </div>
        <div class="cost-row" v-for="item in featureCostItems" :key="item.action">
          <span class="c-name">{{ item.label }}</span>
          <span class="c-credits">{{ item.credits }} credit{{ item.credits > 1 ? 's' : '' }}</span>
          <span class="c-yuan">¥{{ item.yuan }}</span>
        </div>
      </div>
    </div>

    <!-- 支付方式选择弹窗 -->
    <el-dialog v-model="paymentDialogVisible" title="选择支付方式" width="500px" :close-on-click-modal="false">
      <div class="payment-methods">
        <div class="method-item" :class="{ active: selectedPayMethod === 'wechat' }" @click="handleSelectPayMethod('wechat')">
          <div class="icon wechat-icon">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 5.58 2 10c0 2.54 1.19 4.85 3.15 6.37.22.21.35.52.27.82l-.88 3.13c-.12.43.17.83.6.83.13 0 .26-.03.39-.1l3.46-1.81c.21-.11.46-.13.69-.05 1.33.43 2.75.66 4.22.66 5.52 0 10-3.58 10-8 0-4.42-4.48-8-10-8zm.5 12h-1v1h1v-1zm2 0h-1v1h1v-1zm2 0h-1v1h1v-1zm-6 0h-1v1h1v-1z" fill="#09b81f"/>
            </svg>
          </div>
          <div class="info">
            <h4>微信支付</h4>
            <p>扫码支付</p>
          </div>
          <el-radio v-model="selectedPayMethod" label="wechat"></el-radio>
        </div>
        <div class="method-item" :class="{ active: selectedPayMethod === 'alipay' }" @click="handleSelectPayMethod('alipay')">
          <div class="icon alipay-icon">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6h1.5V7zm2 0h-1.5v6H14.5V7zm-5 0H6v6h3.5V7z" fill="#1677FF"/>
            </svg>
          </div>
          <div class="info">
            <h4>支付宝</h4>
            <p>扫码支付</p>
          </div>
          <el-radio v-model="selectedPayMethod" label="alipay"></el-radio>
        </div>
      </div>
      <template #footer>
        <el-button @click="paymentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmPayment" :loading="payLoading" :disabled="!selectedPayMethod">确认支付</el-button>
      </template>
    </el-dialog>

    <!-- 二维码显示弹窗 -->
    <el-dialog v-model="qrcodeDialogVisible" title="扫码支付" width="400px" :close-on-click-modal="false">
      <div class="qrcode-section">
        <div class="payment-method-badge">
          <span v-if="selectedPayMethod === 'wechat'" class="badge wechat">🔵 微信支付</span>
          <span v-else class="badge alipay">🔵 支付宝</span>
        </div>
        <p class="order-info">订单号: {{ currentOrderNo }}</p>
        <img v-if="currentQrcode" :src="currentQrcode" :alt="'QR Code'" class="qrcode-img" />
        <p class="tips">请用 {{ selectedPayMethod === 'wechat' ? '微信' : '支付宝' }} 扫码支付</p>
        <el-progress :percentage="paymentProgress" :show-text="false" v-if="paymentProgress > 0"></el-progress>
        <p v-if="paymentProgress > 0" class="progress-text">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在等待支付确认... {{ paymentProgress.toFixed(1) }}%
        </p>
      </div>
      <template #footer>
        <el-button @click="qrcodeDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { useBillingStore } from '@/store/modules/billing'
import { useAuthStore } from '@/store/modules/auth'

const billingStore = useBillingStore()
const authStore = useAuthStore()

const perUseQuantity = ref(1)
const paymentDialogVisible = ref(false)
const qrcodeDialogVisible = ref(false)
const selectedPayMethod = ref('wechat')
const buyLoading = ref(false)
const payLoading = ref(false)
const paymentProgress = ref(0)
const currentOrderNo = ref('')
const currentQrcode = ref('')
const currentProductType = ref('')

const pricePerUse = computed(() => {
  return billingStore.pricing?.per_use_yuan || '9.90'
})

const priceMonthly = computed(() => {
  return billingStore.pricing?.monthly_yuan || '69.90'
})

const monthlyLimit = computed(() => {
  return billingStore.pricing?.monthly_limit || 20
})

const featureCostItems = computed(() => {
  return billingStore.featureCosts?.items || []
})

const perUsePrice = computed(() => {
  const price = parseFloat(pricePerUse.value) * perUseQuantity.value
  return price.toFixed(2)
})

onMounted(async () => {
  await Promise.all([
    billingStore.loadPricing(),
    billingStore.loadFeatureCosts(),
  ])
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
  }
})

const selectPayMethod = (method) => {
  selectedPayMethod.value = method
}

const handleSelectPayMethod = async (method) => {
  selectedPayMethod.value = method
  // 立即开始支付流程，点击后直接显示二维码
  await confirmPayment()
}

const buyPerUse = () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  if (!perUseQuantity.value || perUseQuantity.value < 1) {
    perUseQuantity.value = 1
    ElMessage.warning('购买次数最少为1次')
    return
  }
  currentProductType.value = 'per_use'
  paymentDialogVisible.value = true
}

const buyMonthly = () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  currentProductType.value = 'monthly'
  paymentDialogVisible.value = true
}

const confirmPayment = async () => {
  if (!selectedPayMethod.value) {
    ElMessage.warning('请选择支付方式')
    return
  }

  payLoading.value = true
  try {
    const quantity = currentProductType.value === 'per_use' ? perUseQuantity.value : 1
    const order = await billingStore.createOrder(
      currentProductType.value,
      selectedPayMethod.value,
      quantity
    )

    currentOrderNo.value = order.order_no
    currentQrcode.value = order.pay_url

    paymentDialogVisible.value = false
    qrcodeDialogVisible.value = true

    // 启动支付状态轮询
    pollPaymentStatus(order.order_no)
  } catch (e) {
    ElMessage.error('创建订单失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    payLoading.value = false
  }
}

let pollTimer = null

const pollPaymentStatus = (orderNo) => {
  // 清除可能残留的旧轮询
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  paymentProgress.value = 0

  let attempts = 0
  const maxAttempts = 120 // 2分钟（每次1秒）

  pollTimer = setInterval(async () => {
    attempts++
    paymentProgress.value = Math.min((attempts / maxAttempts) * 100, 95)

    try {
      await billingStore.loadOrders()
      const order = billingStore.orders.find(o => o.order_no === orderNo)

      if (order && order.status === 'paid') {
        clearInterval(pollTimer)
        pollTimer = null
        paymentProgress.value = 100
        ElMessage.success('支付成功！')
        setTimeout(() => {
          qrcodeDialogVisible.value = false
          billingStore.loadQuota()
        }, 1500)
        return
      }

      if (attempts >= maxAttempts) {
        clearInterval(pollTimer)
        pollTimer = null
        ElMessage.warning('支付超时，请手动检查订单状态')
      }
    } catch (e) {
      // 轮询中的错误不弹窗
    }
  }, 1000)
}
</script>

<style scoped>
.pricing-page {
  padding: 48px 20px 80px;
  background: transparent;
  min-height: calc(100vh - 80px);
  max-width: 1000px;
  margin: 0 auto;
}

.pricing-header {
  text-align: center;
  margin-bottom: 50px;
}

.pricing-header h1 {
  font-size: 36px;
  font-weight: 400;
  color: rgb(26, 28, 28);
  margin-bottom: 12px;
  line-height: 36px;
}

.pricing-header p {
  color: rgb(107, 114, 128);
  font-size: 16px;
}

.billing-note {
  max-width: 1000px;
  margin: 0 auto 28px;
  padding: 14px 20px;
  background: rgba(0, 108, 73, 0.06);
  border: 1px solid rgba(0, 108, 73, 0.18);
  border-radius: 14px;
  color: rgb(59, 74, 65);
  font-size: 14px;
  line-height: 22px;
  text-align: center;
}

.billing-note strong {
  color: rgb(0, 108, 73);
  font-weight: 600;
}

.pricing-container {
  max-width: 1000px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

/* 各功能消耗对照表 */
.cost-table-section {
  max-width: 680px;
  margin: 56px auto 0;
  text-align: center;
}

.cost-table-section h2 {
  font-size: 24px;
  font-weight: 400;
  color: rgb(26, 28, 28);
  margin-bottom: 8px;
}

.cost-table-sub {
  color: rgb(107, 114, 128);
  font-size: 14px;
  margin-bottom: 24px;
}

.cost-table {
  border: 1px solid rgba(186, 202, 191, 0.4);
  border-radius: 16px;
  overflow: hidden;
}

.cost-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  align-items: center;
  padding: 14px 24px;
  font-size: 15px;
  color: rgb(26, 28, 28);
  border-bottom: 1px solid rgba(186, 202, 191, 0.25);
}

.cost-row:last-child {
  border-bottom: none;
}

.cost-row.cost-head {
  background: rgb(243, 243, 244);
  font-weight: 600;
  color: rgb(59, 74, 65);
  font-size: 14px;
}

.cost-row .c-name {
  text-align: left;
}

.cost-row .c-credits {
  color: rgb(0, 108, 73);
  font-weight: 500;
}

.cost-row .c-yuan {
  text-align: right;
  color: rgb(59, 74, 65);
}

.pricing-card {
  background: rgb(243, 243, 244);
  border-radius: 48px;
  padding: 48px;
  border: 1px solid rgba(186, 202, 191, 0.10);
  box-shadow: none;
  transition: transform 0.22s, box-shadow 0.22s;
  position: relative;
  overflow: hidden;
}

.pricing-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.10);
}

.pricing-card.recommended {
  background: rgb(0, 108, 73);
  border: none;
  box-shadow: 0 16px 48px rgba(0, 108, 73, 0.35);
  transform: none;
  color: white;
}

.pricing-card.recommended:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 56px rgba(0, 108, 73, 0.40);
}

.ribbon {
  position: absolute;
  top: 20px;
  right: 20px;
  background: transparent;
  color: rgb(79, 251, 182);
  padding: 0;
  border-radius: 0;
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 1.2px;
}

.card-title {
  text-align: left;
  margin-bottom: 20px;
}

.card-title h3 {
  font-size: 36px;
  font-weight: 400;
  margin-bottom: 10px;
  color: rgb(26, 28, 28);
  line-height: 40px;
}

.pricing-card.recommended .card-title h3 {
  color: white;
}

.price {
  font-family: 'Newsreader', serif;
  font-size: 48px;
  color: rgb(26, 28, 28);
  font-weight: 400;
  margin: 24px 0;
}

.pricing-card.recommended .price {
  color: white;
}

.currency {
  font-size: 20px;
  margin-right: 5px;
}

.amount {
  margin-right: 5px;
}

.unit {
  font-size: 20px;
  color: rgb(59, 74, 65);
}

.pricing-card.recommended .unit {
  color: rgba(255, 255, 255, 0.8);
}

.card-content {
  padding-top: 0;
  border-top: none;
}

.desc {
  text-align: left;
  color: rgb(59, 74, 65);
  margin-bottom: 20px;
  font-size: 16px;
  font-family: 'Manrope', sans-serif;
  line-height: 24px;
}

.pricing-card.recommended .desc {
  color: rgba(255, 255, 255, 0.8);
}

.features {
  margin-bottom: 25px;
}

.feature {
  padding: 8px 0;
  color: rgb(26, 28, 28);
  font-size: 16px;
  line-height: 24px;
}

.pricing-card.recommended .feature {
  color: white;
}

.payment-methods {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 20px 0;
}

.method-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border: 2px solid rgba(229, 231, 235, 0.50);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.method-item:hover {
  border-color: rgb(0, 108, 73);
  background: rgba(79, 251, 182, 0.05);
}

.method-item.active {
  border-color: rgb(0, 108, 73);
  background: rgba(79, 251, 182, 0.05);
}

.method-item .icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  border-radius: 8px;
  flex-shrink: 0;
}

.method-item .wechat-icon {
  background: #f0f9ff;
}

.method-item .wechat-icon svg {
  width: 24px;
  height: 24px;
}

.method-item .alipay-icon {
  background: #f0f5ff;
}

.method-item .alipay-icon svg {
  width: 24px;
  height: 24px;
}

.method-item .info {
  flex: 1;
}

.method-item h4 {
  margin: 0;
  font-size: 14px;
  font-weight: bold;
}

.method-item p {
  margin: 4px 0 0 0;
  color: #999;
  font-size: 12px;
}

.qrcode-section {
  text-align: center;
  padding: 20px 0;
}

.payment-method-badge {
  margin-bottom: 20px;
}

.badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.badge.wechat {
  background: #f0f9ff;
  color: #09b81f;
}

.badge.alipay {
  background: #f0f5ff;
  color: #1677ff;
}

.order-info {
  color: #666;
  font-size: 12px;
  margin-bottom: 15px;
}

.qrcode-img {
  max-width: 100%;
  width: 250px;
  height: 250px;
  border: 2px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: 15px;
}

.tips {
  color: #999;
  font-size: 14px;
  margin-bottom: 15px;
}

.progress-text {
  color: #006C49;
  font-size: 12px;
  margin-top: 10px;
}
</style>
