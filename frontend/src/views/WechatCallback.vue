<template>
  <div class="callback-page">
    <div class="callback-container">
      <el-result
        v-if="!isLoading"
        :icon="statusIcon"
        :title="statusTitle"
        :sub-title="statusMessage"
      >
        <template #extra>
          <el-button type="primary" @click="handleRedirect">
            {{ buttonText }}
          </el-button>
        </template>
      </el-result>

      <div v-else class="loading-state">
        <el-spin />
        <p>正在处理微信授权...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isLoading = ref(true)
const isSuccess = ref(false)
const errorMessage = ref('')

const statusIcon = computed(() => isSuccess.value ? 'success' : 'error')
const statusTitle = computed(() => isSuccess.value ? '登录成功' : '登录失败')
const statusMessage = computed(() => isSuccess.value ? '即将跳转到首页...' : errorMessage.value)
const buttonText = computed(() => isSuccess.value ? '返回首页' : '重新登录')

async function processCallback() {
  const code = route.query.code
  const state = route.query.state || 'login'

  if (!code) {
    errorMessage.value = '无效的回调参数，缺少授权码'
    isLoading.value = false
    return
  }

  try {
    // 后端验证 code 并创建用户 + 返回 token
    const response = await axios.get('/api/v1/auth/wechat/callback', {
      params: { code, state }
    })

    const token = response.data.access_token
    await authStore.loginWithToken(token)

    isSuccess.value = true
    ElMessage.success('微信登录成功！')

    // 2秒后自动跳转
    setTimeout(() => {
      const redirect = state === 'login' ? '/' : decodeURIComponent(state)
      router.push(redirect)
    }, 2000)
  } catch (error) {
    isSuccess.value = false
    const detail = error.response?.data?.detail
    errorMessage.value = detail || '微信授权失败，请检查配置是否正确'
    console.error('[WechatCallback] Error:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  processCallback()
})

function handleRedirect() {
  if (isSuccess.value) {
    router.push('/')
  } else {
    router.push('/login')
  }
}
</script>

<style scoped>
.callback-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #006C49 0%, #004d35 100%);
}

.callback-container {
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: white;
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.loading-state p {
  color: #333;
  font-size: 16px;
  margin: 0;
}
</style>
