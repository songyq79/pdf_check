<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <span class="logo-vr">VR</span><span class="logo-only">only</span>
        <p class="logo-sub">论文评价检验系统</p>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <!-- 登录 -->
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" @submit.prevent="handleLogin">
            <el-form-item prop="username">
              <el-input v-model="loginForm.username" placeholder="用户名" size="large" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large"
                prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
            </el-form-item>
            <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleLogin">
              登录
            </el-button>
          </el-form>

          <!-- 其他登录方式 -->
          <div class="other-login-methods">
            <div class="divider-text">其他登录方式</div>
            <div class="login-icons">
              <button class="login-icon wechat" @click="handleWechatLogin" :disabled="loading" title="微信登录">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2C6.48 2 2 5.58 2 10c0 2.54 1.19 4.85 3.15 6.37.22.21.35.52.27.82l-.88 3.13c-.12.43.17.83.6.83.13 0 .26-.03.39-.1l3.46-1.81c.21-.11.46-.13.69-.05 1.33.43 2.75.66 4.22.66 5.52 0 10-3.58 10-8 0-4.42-4.48-8-10-8zm.5 12h-1v1h1v-1zm2 0h-1v1h1v-1zm2 0h-1v1h1v-1zm-6 0h-1v1h1v-1z" fill="white"/>
                </svg>
              </button>
            </div>
          </div>
        </el-tab-pane>

        <!-- 手机号登录 -->
        <el-tab-pane label="手机号登录" name="phone">
          <el-form :model="phoneForm" :rules="phoneRules" ref="phoneFormRef">
            <el-form-item prop="phone">
              <el-input v-model="phoneForm.phone" placeholder="请输入手机号" size="large" prefix-icon="Phone" />
            </el-form-item>
            <el-form-item prop="code">
              <div class="code-input-group">
                <el-input v-model="phoneForm.code" placeholder="请输入验证码" size="large" />
                <el-button
                  :disabled="!isPhoneValid || smsSending || smsCountdown > 0"
                  @click="handleSendSms"
                  :loading="smsSending"
                  class="send-code-btn">
                  {{ smsCountdown > 0 ? `${smsCountdown}s` : '发送验证码' }}
                </el-button>
              </div>
            </el-form-item>
            <el-collapse>
              <el-collapse-item title="邀请码（可选）" name="1">
                <el-form-item prop="inviteCode">
                  <el-input v-model="phoneForm.inviteCode" placeholder="输入邀请码（可选）" size="large" />
                </el-form-item>
              </el-collapse-item>
            </el-collapse>
            <el-button type="primary" size="large" style="width:100%; margin-top: 20px" :loading="loading" @click="handlePhoneLogin">
              登录
            </el-button>
          </el-form>

          <!-- 其他登录方式 -->
          <div class="other-login-methods">
            <div class="divider-text">其他登录方式</div>
            <div class="login-icons">
              <button class="login-icon wechat" @click="handleWechatLogin" :disabled="loading" title="微信登录">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2C6.48 2 2 5.58 2 10c0 2.54 1.19 4.85 3.15 6.37.22.21.35.52.27.82l-.88 3.13c-.12.43.17.83.6.83.13 0 .26-.03.39-.1l3.46-1.81c.21-.11.46-.13.69-.05 1.33.43 2.75.66 4.22.66 5.52 0 10-3.58 10-8 0-4.42-4.48-8-10-8zm.5 12h-1v1h1v-1zm2 0h-1v1h1v-1zm2 0h-1v1h1v-1zm-6 0h-1v1h1v-1z" fill="white"/>
                </svg>
              </button>
            </div>
          </div>
        </el-tab-pane>

        <!-- 注册 -->
        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef">
            <el-form-item prop="username">
              <el-input v-model="registerForm.username" placeholder="用户名（4-20位字母数字）" size="large" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="email">
              <el-input v-model="registerForm.email" placeholder="邮箱（选填）" size="large" prefix-icon="Message" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="registerForm.password" type="password" placeholder="密码（至少6位）" size="large"
                prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" size="large"
                prefix-icon="Lock" show-password @keyup.enter="handleRegister" />
            </el-form-item>
            <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleRegister">
              提交注册申请
            </el-button>
            <p class="register-tip">注册后需等待管理员审批，审批通过后方可登录</p>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <div class="back-link">
        <el-button link @click="router.push('/')">← 返回首页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/modules/auth'
import { register, sendSmsCode, smsLogin, getWechatLoginUrl } from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)

// 登录表单
const loginFormRef = ref()
const loginForm = reactive({ username: '', password: '' })
const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 手机号登录表单
const phoneFormRef = ref()
const phoneForm = reactive({ phone: '', code: '', inviteCode: '' })
const phoneRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为6位数字', trigger: 'blur' },
  ],
}

// 注册表单
const registerFormRef = ref()
const registerForm = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 20, message: '用户名4-20位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) callback(new Error('两次密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

// 短信相关状态
const smsSending = ref(false)
const smsCountdown = ref(0)
let smsTimer = null

const isPhoneValid = computed(() => /^1[3-9]\d{9}$/.test(phoneForm.phone))

async function handleLogin() {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await authStore.loginAction(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    const redirect = router.currentRoute.value.query.redirect
    router.push(redirect ? String(redirect) : '/')
  } catch (e) {
    const msg = e.response?.data?.detail || '登录失败，请检查用户名和密码'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

async function handleSendSms() {
  if (!isPhoneValid.value) {
    ElMessage.error('请输入正确的手机号')
    return
  }

  smsSending.value = true
  try {
    await sendSmsCode(phoneForm.phone)
    ElMessage.success('验证码已发送，请查看短信')
    // 启动60秒倒计时
    smsCountdown.value = 60
    smsTimer = setInterval(() => {
      smsCountdown.value--
      if (smsCountdown.value <= 0) {
        clearInterval(smsTimer)
      }
    }, 1000)
  } catch (e) {
    const msg = e.response?.data?.detail || '发送验证码失败'
    ElMessage.error(msg)
  } finally {
    smsSending.value = false
  }
}

async function handlePhoneLogin() {
  const valid = await phoneFormRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await smsLogin(phoneForm.phone, phoneForm.code, phoneForm.inviteCode)
    await authStore.loginWithToken(res.data.access_token)
    ElMessage.success('登录成功')
    const redirect = router.currentRoute.value.query.redirect
    router.push(redirect ? String(redirect) : '/')
  } catch (e) {
    const msg = e.response?.data?.detail || '登录失败，请检查验证码'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await register(registerForm.username, registerForm.password, registerForm.email)
    ElMessage.success('注册申请已提交，请等待管理员审批')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
  } catch (e) {
    const msg = e.response?.data?.detail || '注册失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

async function handleWechatLogin() {
  try {
    const res = await getWechatLoginUrl()
    window.location.href = res.data.url
  } catch (e) {
    const msg = e.response?.data?.detail || '获取微信登录URL失败'
    ElMessage.error(msg)
  }
}

onUnmounted(() => {
  if (smsTimer) {
    clearInterval(smsTimer)
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #006C49 0%, #004d35 100%);
}

.login-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.login-logo {
  text-align: center;
  margin-bottom: 30px;
}

.logo-vr {
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(135deg, #006C49 0%, #004d35 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-only {
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(135deg, #006C49 0%, #004d35 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-sub {
  color: #999;
  font-size: 14px;
  margin-top: 6px;
}

.login-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.login-tabs :deep(.el-form-item) {
  margin-bottom: 18px;
}

.register-tip {
  font-size: 12px;
  color: #999;
  text-align: center;
  margin-top: 12px;
  line-height: 1.6;
}

.back-link {
  text-align: center;
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

/* 其他登录方式 */
.other-login-methods {
  margin-top: 24px;
  text-align: center;
}

.divider-text {
  font-size: 12px;
  color: #999;
  margin-bottom: 16px;
  position: relative;
}

.divider-text::before,
.divider-text::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 35%;
  height: 1px;
  background: #ddd;
}

.divider-text::before {
  left: 0;
}

.divider-text::after {
  right: 0;
}

.login-icons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.login-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  color: white;
  padding: 0;
}

.login-icon svg {
  width: 24px;
  height: 24px;
}

.login-icon:hover:not(:disabled) {
  border-color: #006C49;
  background: #006C49;
  box-shadow: 0 2px 12px rgba(0, 108, 73, 0.3);
}

.login-icon:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-icon.wechat {
  background: #09b81f;
  border-color: #09b81f;
}

.login-icon.wechat:hover:not(:disabled) {
  background: #0a9918;
  border-color: #0a9918;
  box-shadow: 0 2px 12px rgba(9, 184, 31, 0.3);
}

/* 手机号验证码输入组 */
.code-input-group {
  display: flex;
  gap: 8px;
}

.code-input-group :deep(.el-input) {
  flex: 1;
}

.send-code-btn {
  min-width: 110px;
}

/* 折叠面板优化 */
.login-tabs :deep(.el-collapse) {
  border: 1px solid #f0f0f0;
  background: #fafafa;
}

.login-tabs :deep(.el-collapse-item__header) {
  font-size: 12px;
  color: #999;
}

.login-tabs :deep(.el-collapse-item__content) {
  padding-bottom: 0;
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    width: 100%;
    margin: 0 20px;
    padding: 30px 20px;
  }

  .code-input-group {
    flex-direction: column;
  }

  .send-code-btn {
    width: 100%;
  }
}
</style>
