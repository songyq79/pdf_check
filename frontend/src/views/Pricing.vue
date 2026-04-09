<template>
  <div class="pricing-page">
    <div class="pricing-header">
      <h1>选择适合你的套餐</h1>
      <p>开启无限可能的学术之旅</p>
    </div>

    <div class="pricing-container">
      <!-- 按次购买 -->
      <div class="pricing-card pay-per-use">
        <div class="card-title">
          <h3>按次购买</h3>
          <p class="price">
            <span class="currency">¥</span><span class="amount">{{ pricePerUse }}</span><span class="unit">/次</span>
          </p>
        </div>
        <div class="card-content">
          <p class="desc">随用随买，灵活使用</p>
          <div class="features">
            <div class="feature">✓ 任意功能可用</div>
            <div class="feature">✓ 使用即扣</div>
            <div class="feature">✓ 无过期限制</div>
          </div>
          <el-input-number v-model="perUseQuantity" :min="1" :max="100" style="width: 100%; margin-bottom: 15px;">
          </el-input-number>
          <el-button type="primary" size="large" style="width: 100%;" @click="buyPerUse" :loading="buyLoading">
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
          <p class="desc">全功能无限使用</p>
          <div class="features">
            <div class="feature">✓ 所有功能无限用</div>
            <div class="feature">✓ 优先客服支持</div>
            <div class="feature">✓ 30天有效期</div>
            <div class="feature">✓ 支持续费累计</div>
          </div>
          <el-button type="primary" size="large" style="width: 100%; background: linear-gradient(135deg, #006C49, #004d35); border: none;"
            @click="buyMonthly" :loading="buyLoading">
            立即订阅
          </el-button>
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
        <el-progress :percentage="paymentProgress" v-if="paymentProgress > 0"></el-progress>
        <p v-if="paymentProgress > 0" class="progress-text">{{ paymentProgress }}% - 请稍候...</p>
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
  return billingStore.pricing?.per_use_yuan || '3.00'
})

const priceMonthly = computed(() => {
  return billingStore.pricing?.monthly_yuan || '99.00'
})

const perUsePrice = computed(() => {
  const price = parseFloat(pricePerUse.value) * perUseQuantity.value
  return price.toFixed(2)
})

onMounted(async () => {
  await billingStore.loadPricing()
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

const pollPaymentStatus = async (orderNo) => {
  let attempts = 0
  const maxAttempts = 120 // 2分钟（每次1秒）

  const timer = setInterval(async () => {
    attempts++
    paymentProgress.value = Math.min((attempts / maxAttempts) * 100, 95)

    try {
      await billingStore.loadOrders()
      const order = billingStore.orders.find(o => o.order_no === orderNo)

      if (order && order.status === 'paid') {
        clearInterval(timer)
        paymentProgress.value = 100
        ElMessage.success('支付成功！')
        setTimeout(() => {
          qrcodeDialogVisible.value = false
          billingStore.loadQuota()
        }, 1500)
        return
      }

      if (attempts >= maxAttempts) {
        clearInterval(timer)
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
  padding: 60px 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 60px);
}

.pricing-header {
  text-align: center;
  margin-bottom: 50px;
}

.pricing-header h1 {
  font-size: 36px;
  color: #333;
  margin-bottom: 10px;
}

.pricing-header p {
  color: #666;
  font-size: 16px;
}

.pricing-container {
  max-width: 1000px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
}

.pricing-card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s, box-shadow 0.3s;
  position: relative;
}

.pricing-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.pricing-card.recommended {
  border: 2px solid #006C49;
  transform: scale(1.05);
}

.pricing-card.recommended:hover {
  transform: scale(1.05) translateY(-5px);
}

.ribbon {
  position: absolute;
  top: 20px;
  right: -5px;
  background: linear-gradient(135deg, #006C49 0%, #004d35 100%);
  color: white;
  padding: 6px 20px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.card-title {
  text-align: center;
  margin-bottom: 20px;
}

.card-title h3 {
  font-size: 20px;
  margin-bottom: 10px;
  color: #333;
}

.price {
  font-size: 32px;
  color: #006C49;
  font-weight: bold;
  margin: 0;
}

.currency {
  font-size: 20px;
  margin-right: 5px;
}

.amount {
  margin-right: 5px;
}

.unit {
  font-size: 14px;
  color: #999;
}

.card-content {
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.desc {
  text-align: center;
  color: #666;
  margin-bottom: 20px;
  font-size: 14px;
}

.features {
  margin-bottom: 25px;
}

.feature {
  padding: 8px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
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
  border: 2px solid #f0f0f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.method-item:hover {
  border-color: #006C49;
  background: #f0faf7;
}

.method-item.active {
  border-color: #006C49;
  background: #f0faf7;
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
