<template>
  <div class="user-center">
    <div class="container">
      <h1>用户中心</h1>

      <!-- 续费充值卡片 -->
      <div class="recharge-section">
        <el-card class="recharge-card">
          <template #header>
            <div class="card-header">
              <span>💳 续费充值</span>
            </div>
          </template>

          <div class="recharge-content">
            <p class="recharge-desc">选择适合你的方案，获得更多使用次数或全功能订阅</p>

            <div class="recharge-options">
              <!-- 按次购买 -->
              <div class="recharge-option">
                <div class="option-header">
                  <h4>按次购买</h4>
                  <span class="price">¥{{ billingStore.pricing?.per_use_yuan || '3.00' }}/次</span>
                </div>
                <p class="option-desc">随用随买，灵活使用</p>
                <el-button type="primary" @click="goToPricing" size="small">去购买</el-button>
              </div>

              <!-- 包月订阅 -->
              <div class="recharge-option recommended">
                <div class="option-header">
                  <h4>包月订阅</h4>
                  <span class="price">¥{{ billingStore.pricing?.monthly_yuan || '99.00' }}/月</span>
                </div>
                <p class="option-desc">全功能无限使用，优先支持</p>
                <el-button type="primary" @click="goToPricing" size="small">立即订阅</el-button>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 权益卡片 -->
      <div class="quota-section">
        <el-card class="quota-card">
          <template #header>
            <div class="card-header">
              <span>我的权益</span>
              <el-button size="small" link @click="billingStore.loadQuota()">刷新</el-button>
            </div>
          </template>

          <!-- 订阅信息 -->
          <div v-if="billingStore.subscription" class="subscription-info">
            <el-alert title="✨ 包月订阅生效" type="success" :closable="false">
              <p>有效期至: {{ formatDate(billingStore.subscription.expires_at) }}</p>
              <p>剩余 {{ billingStore.subscription.days_remaining }} 天</p>
            </el-alert>
          </div>

          <!-- 额度余额 -->
          <div class="credits-info">
            <div class="credit-item">
              <span class="label">剩余额度</span>
              <span class="value">{{ billingStore.totalCredits }} 次</span>
            </div>
          </div>

          <!-- 明细 -->
          <div class="credits-detail" v-if="billingStore.quota?.credits">
            <div v-for="(count, source) in billingStore.quota.credits" :key="source" class="detail-row">
              <span class="source-label">{{ formatSourceLabel(source) }}</span>
              <span class="count">{{ count }} 次</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 邀请码 -->
      <div class="invite-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>邀请好友</span>
              <el-button type="primary" size="small" @click="handleGenerateCode" :loading="inviteLoading">
                生成邀请码
              </el-button>
            </div>
          </template>

          <p class="invite-desc">
            将邀请码分享给好友，好友<strong>首次注册时填写您的邀请码</strong>后，您将自动获得 3 次使用额度。
            好友注册成功后，请点击"我的权益"的刷新按钮查看最新余额。
          </p>

          <el-table :data="pagedInviteCodes" stripe v-if="billingStore.inviteCodes.length > 0">
            <el-table-column prop="code" label="邀请码" width="120"></el-table-column>
            <el-table-column label="使用状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.used_by_id" type="success">已使用</el-tag>
                <el-tag v-else type="info">待使用</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="使用时间" width="160">
              <template #default="{ row }">
                {{ row.used_at ? formatDate(row.used_at) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="生成时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="copyCode(row.code)">
                  复制
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-if="billingStore.inviteCodes.length > invitePageSize"
            v-model:current-page="invitePage"
            :page-size="invitePageSize"
            :total="billingStore.inviteCodes.length"
            layout="prev, pager, next"
            class="order-pagination"
          />

          <el-empty v-else-if="billingStore.inviteCodes.length === 0" description="还没有生成邀请码"></el-empty>
        </el-card>
      </div>

      <!-- 我的订单 -->
      <div class="orders-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>💰 我的订单</span>
            </div>
          </template>

          <el-table :data="pagedOrders" stripe v-if="orders.length > 0">
            <el-table-column prop="order_no" label="订单号" width="200" />
            <el-table-column label="套餐类型" width="120">
              <template #default="{ row }">
                {{ row.product_type === 'monthly' ? '包月订阅' : `按次购买(${row.quantity}次)` }}
              </template>
            </el-table-column>
            <el-table-column label="金额" width="80">
              <template #default="{ row }">
                ¥{{ (row.amount_cents / 100).toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'paid'" type="success">已支付</el-tag>
                <el-tag v-else-if="row.status === 'pending'" type="warning">待支付</el-tag>
                <el-tag v-else-if="row.status === 'refund_pending'" type="info">审核中</el-tag>
                <el-tag v-else-if="row.status === 'refunded'" type="">已退款</el-tag>
                <el-tag v-else>{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="下单时间" width="160">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <template v-if="row.status === 'paid'">
                  <el-button type="primary" size="small" @click="handleShowRefundDialog(row)">
                    申请退款
                  </el-button>
                </template>
                <template v-else-if="row.status === 'refund_pending'">
                  <el-tag type="warning">审核中</el-tag>
                </template>
                <template v-else-if="row.refund_reject_reason && row.status === 'paid'">
                  <div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;">
                    <el-tooltip :content="`拒绝原因: ${row.refund_reject_reason}`" placement="top">
                      <el-tag type="danger" size="small">已拒绝</el-tag>
                    </el-tooltip>
                    <el-button type="primary" size="small" @click="handleShowRefundDialog(row)">
                      重新申请
                    </el-button>
                  </div>
                </template>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="orders.length > orderPageSize"
            v-model:current-page="orderPage"
            :page-size="orderPageSize"
            :total="orders.length"
            layout="prev, pager, next"
            class="order-pagination"
          />
          <el-empty v-else-if="orders.length === 0" description="暂无订单"></el-empty>
        </el-card>
      </div>

    </div>

    <!-- 申请退款 dialog -->
    <el-dialog v-model="showRefundDialog" title="申请退款" width="400px" :close-on-click-modal="false">
      <div v-if="currentOrder" class="refund-dialog-content">
        <div class="order-info">
          <div class="info-row">
            <span class="label">订单号:</span>
            <span class="value">{{ currentOrder.order_no }}</span>
          </div>
          <div class="info-row">
            <span class="label">金额:</span>
            <span class="value">¥{{ (currentOrder.amount_cents / 100).toFixed(2) }}</span>
          </div>
        </div>
        <el-form>
          <el-form-item label="退款原因" required>
            <el-input
              v-model="refundForm.reason"
              type="textarea"
              placeholder="请详细说明退款原因（至少10字）"
              :rows="4"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showRefundDialog = false">取消</el-button>
        <el-button type="primary" :loading="refundLoading" @click="handleApplyRefund">
          提交申请
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useBillingStore } from '@/store/modules/billing'
import { getMyOrders, applyRefund } from '@/api/billing'

const router = useRouter()
const billingStore = useBillingStore()

const inviteLoading = ref(false)
const invitePage = ref(1)
const invitePageSize = 5
const pagedInviteCodes = computed(() => {
  const start = (invitePage.value - 1) * invitePageSize
  return billingStore.inviteCodes.slice(start, start + invitePageSize)
})
const orders = ref([])
const orderPage = ref(1)
const orderPageSize = 10
const pagedOrders = computed(() => {
  const start = (orderPage.value - 1) * orderPageSize
  return orders.value.slice(start, start + orderPageSize)
})
const showRefundDialog = ref(false)
const refundForm = ref({ reason: '' })
const currentOrder = ref(null)
const refundLoading = ref(false)

onMounted(() => {
  billingStore.loadPricing()
  billingStore.loadQuota()
  billingStore.loadInviteCodes()
  loadOrders()
})

async function loadOrders() {
  try {
    const res = await getMyOrders()
    orders.value = res.data || []
  } catch (e) {
    ElMessage.error('加载订单列表失败')
  }
}

const formatDate = (date) => {
  if (!date) return '-'
  // 后端存储 UTC 时间，字符串末尾无 'Z'，需手动补偿 +8 小时转为北京时间
  const str = String(date)
  const d = str.endsWith('Z') || str.includes('+') ? new Date(date) : new Date(date + 'Z')
  return d.toLocaleString('zh-CN')
}

const formatSourceLabel = (source) => {
  const labels = {
    free: '免费试用',
    purchase: '按次购买',
    referral: '邀请奖励',
    subscription: '包月订阅',
  }
  return labels[source] || source
}

const handleGenerateCode = async () => {
  inviteLoading.value = true
  try {
    const code = await billingStore.genInviteCode()
    ElMessage.success(`邀请码已生成: ${code}`)
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    inviteLoading.value = false
  }
}

const copyCode = (code) => {
  navigator.clipboard.writeText(code)
  ElMessage.success('已复制到剪贴板')
}

const goToPricing = () => {
  router.push('/pricing')
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleShowRefundDialog(row) {
  currentOrder.value = row
  refundForm.value = { reason: '' }
  showRefundDialog.value = true
}

async function handleApplyRefund() {
  if (!refundForm.value.reason || refundForm.value.reason.trim().length === 0) {
    ElMessage.error('请输入退款原因')
    return
  }

  refundLoading.value = true
  try {
    await applyRefund(currentOrder.value.order_no, refundForm.value.reason)
    ElMessage.success('退款申请已提交，请等待管理员审核')
    showRefundDialog.value = false
    loadOrders()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '申请失败')
  } finally {
    refundLoading.value = false
  }
}
</script>

<style scoped>
.user-center {
  padding: 30px 0;
  background: rgb(249, 249, 249);
  min-height: calc(100vh - 60px);
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
}

h1 {
  margin-bottom: 30px;
  color: rgb(18, 18, 18);
  font-weight: 400;
}

.recharge-section,
.quota-section,
.invite-section,
.order-pagination {
  margin-top: 16px;
  justify-content: center;
  --el-color-primary: rgb(0, 108, 73);
  --el-color-primary-light-9: rgba(0, 108, 73, 0.1);
}

.orders-section {
  margin-bottom: 30px;
}

.recharge-card {
  background: white;
  border: 1px solid rgba(229, 231, 235, 0.50);
  border-radius: 32px;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
}

.recharge-card :deep(.el-card__header) {
  background: transparent;
  border: none;
  color: rgb(18, 18, 18);
  font-size: 16px;
  font-weight: 500;
}

.recharge-card :deep(.el-card__body) {
  color: rgb(26, 28, 28);
}

.recharge-content {
  padding: 20px 0;
}

.recharge-desc {
  text-align: center;
  color: rgb(107, 114, 128);
  margin-bottom: 25px;
  font-size: 14px;
}

.recharge-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.recharge-option {
  background: rgb(249, 249, 249);
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  color: rgb(26, 28, 28);
  border: 2px solid rgba(229, 231, 235, 0.50);
  transition: all 0.3s;
}

.recharge-option:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.recharge-option.recommended {
  border-color: rgb(0, 108, 73);
  background: white;
}

.recharge-option :deep(.el-button) {
  border-radius: 9999px;
  width: 100%;
  height: 32px;
}

.option-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.option-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: rgb(18, 18, 18);
}

.price {
  font-size: 14px;
  color: rgb(0, 108, 73);
  font-weight: bold;
}

.option-desc {
  font-size: 12px;
  color: rgb(107, 114, 128);
  margin-bottom: 15px;
}

.quota-card {
  background: white;
  border: 1px solid rgba(229, 231, 235, 0.50);
  border-radius: 32px;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
}

.quota-card :deep(.el-card__header) {
  background: transparent;
  border: none;
  color: rgb(18, 18, 18);
}

.quota-card :deep(.el-card__body) {
  color: rgb(26, 28, 28);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.subscription-info {
  margin-bottom: 20px;
}

.subscription-info p {
  margin: 6px 0;
  font-size: 14px;
}

.credits-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px 0;
  border-bottom: 1px solid rgba(229, 231, 235, 0.60);
}

.credit-item {
  display: flex;
  flex-direction: column;
}

.credit-item .label {
  font-size: 12px;
  color: rgb(107, 114, 128);
}

.credit-item .value {
  font-size: 28px;
  font-weight: bold;
  color: rgb(0, 108, 73);
  margin-top: 5px;
}

.credits-detail {
  display: flex;
  gap: 20px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 0;
}

.source-label {
  color: rgb(107, 114, 128);
  font-size: 13px;
}

.count {
  font-weight: bold;
  color: rgb(18, 18, 18);
}

.invite-desc {
  color: rgb(107, 114, 128);
  margin-bottom: 15px;
}

:deep(.el-card) {
  border-radius: 32px;
  border: 1px solid rgba(229, 231, 235, 0.50);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
}

:deep(.el-table) {
  background: transparent;
}

:deep(.el-table thead) {
  background: rgb(249, 249, 249);
}

:deep(.el-table th) {
  background-color: rgb(249, 249, 249);
}

:deep(.el-empty) {
  padding: 40px 0;
}

code {
  background: rgb(249, 249, 249);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  color: rgb(107, 114, 128);
}

.refund-dialog-content {
  padding: 10px 0;
}

.order-info {
  margin-bottom: 20px;
  padding: 12px;
  background: rgb(249, 249, 249);
  border-radius: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  color: rgb(107, 114, 128);
}

.info-row .value {
  font-weight: 500;
  color: rgb(18, 18, 18);
}

/* 响应式 */
@media (max-width: 768px) {
  .recharge-options {
    grid-template-columns: 1fr;
  }
}
</style>
