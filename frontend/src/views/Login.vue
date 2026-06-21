<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <span class="logo-vr">VR</span><span class="logo-only">only</span>
        <p class="logo-sub">论文评价检验系统</p>
      </div>

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
        <el-form-item prop="inviteCode">
          <el-input v-model="phoneForm.inviteCode" placeholder="邀请码（可选）" size="large" autocomplete="off" />
        </el-form-item>
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

      <!-- 机构学生注册 -->
      <div v-if="showInstReg" class="admin-login-form">
        <el-divider>机构学生注册</el-divider>
        <div v-if="instDone" class="inst-done">
          <div class="inst-done-icon">⏳</div>
          <p class="inst-done-title">注册成功，等待机构管理员审批</p>
          <p class="inst-done-sub">审批通过后，用下方「机构账号登录」即可使用（额度由学校统一提供）。</p>
        </div>
        <el-form v-else :model="instForm" :rules="instRules" ref="instFormRef">
          <el-form-item prop="invite_code">
            <el-input v-model="instForm.invite_code" placeholder="机构邀请码（学校发放，8 位）" size="large" />
          </el-form-item>
          <el-form-item prop="username">
            <el-input v-model="instForm.username" placeholder="设置用户名" size="large" prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="instForm.password" type="password" placeholder="设置密码（≥6位）" size="large" prefix-icon="Lock" show-password />
          </el-form-item>
          <div class="code-input-group">
            <el-input v-model="instForm.student_id" placeholder="学号（选填）" size="large" />
            <el-input v-model="instForm.college" placeholder="学院（选填）" size="large" />
          </div>
          <el-button type="primary" size="large" style="width:100%; margin-top:16px" :loading="loading" @click="handleInstRegister">
            注册（需机构审批）
          </el-button>
        </el-form>
      </div>

      <!-- 管理员登录入口 -->
      <div v-if="showAdminLogin" class="admin-login-form">
        <el-divider>管理员登录</el-divider>
        <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef">
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
      </div>

      <div class="back-link">
        <el-button link @click="router.push('/')">← 返回首页</el-button>
        <div class="entry-btns">
          <el-button link class="admin-entry-btn" @click="toggleInstReg">
            🏫 {{ showInstReg ? '收起' : '机构学生' }}
          </el-button>
          <el-button link class="admin-entry-btn" @click="toggleAdmin">
            🔒 {{ showAdminLogin ? '收起' : '账号登录' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/modules/auth'
import { sendSmsCode, smsLogin, getWechatLoginUrl } from '@/api/auth'
import institutionAPI from '@/api/institution'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

// 机构学生注册
const showInstReg = ref(false)
const instDone = ref(false)
const instFormRef = ref()
const instForm = reactive({ invite_code: '', username: '', password: '', student_id: '', college: '' })
const instRules = {
  invite_code: [{ required: true, message: '请输入机构邀请码', trigger: 'blur' }],
  username: [{ required: true, message: '请设置用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
}

function toggleInstReg() {
  showInstReg.value = !showInstReg.value
  if (showInstReg.value) showAdminLogin.value = false
  instDone.value = false
}
function toggleAdmin() {
  showAdminLogin.value = !showAdminLogin.value
  if (showAdminLogin.value) showInstReg.value = false
}

async function handleInstRegister() {
  const valid = await instFormRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await institutionAPI.registerStudent({ ...instForm })
    instDone.value = true
    ElMessage.success('注册成功，等待机构管理员审批')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e._userMessage || '注册失败，请检查邀请码')
  } finally {
    loading.value = false
  }
}

// 管理员登录
const showAdminLogin = ref(false)
const loginFormRef = ref()
const loginForm = reactive({ username: '', password: '' })
const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

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
    ElMessage.error(e.response?.data?.detail || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
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

// 短信相关状态
const smsSending = ref(false)
const smsCountdown = ref(0)
let smsTimer = null

const isPhoneValid = computed(() => /^1[3-9]\d{9}$/.test(phoneForm.phone))

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
    if (res.data.invite_warning) {
      ElMessage.warning(res.data.invite_warning)
    } else {
      ElMessage.success('登录成功')
    }
    const redirect = router.currentRoute.value.query.redirect
    router.push(redirect ? String(redirect) : '/')
  } catch (e) {
    const msg = e.response?.data?.detail || '登录失败，请检查验证码'
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
  background: rgb(249, 249, 249);
}

.login-card {
  background: white;
  border-radius: 32px;
  padding: 48px;
  width: 420px;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(229, 231, 235, 0.50);
}

.login-logo {
  text-align: center;
  margin-bottom: 30px;
}

.logo-vr, .logo-only {
  font-family: 'Newsreader', serif;
  font-size: 28px;
  font-weight: 400;
  font-style: italic;
  color: rgb(24, 24, 27);
  background: none;
  -webkit-background-clip: unset;
  -webkit-text-fill-color: unset;
  background-clip: unset;
}

.logo-sub {
  color: #999;
  font-size: 14px;
  margin-top: 6px;
}

:deep(.el-button--primary) {
  background: rgb(0, 108, 73);
  border-color: rgb(0, 108, 73);
  border-radius: 9999px;
  height: 44px;
  font-size: 16px;
}

:deep(.el-button--primary:hover) {
  background: rgb(0, 90, 60);
  border-color: rgb(0, 90, 60);
}

.admin-login-form {
  margin-top: 16px;
}

.entry-btns {
  display: flex;
  gap: 8px;
}

.inst-done {
  text-align: center;
  padding: 12px 0 4px;
}
.inst-done-icon { font-size: 32px; }
.inst-done-title { font-size: 15px; font-weight: 600; color: rgb(24,24,27); margin: 8px 0 4px; }
.inst-done-sub { font-size: 12px; color: rgb(107,114,128); line-height: 1.6; }

.back-link {
  text-align: center;
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.admin-entry-btn {
  color: rgb(107, 114, 128);
  font-size: 13px;
  border: 1px solid rgba(229, 231, 235, 0.8);
  border-radius: 9999px;
  padding: 4px 12px;
  height: auto;
}

.admin-entry-btn:hover {
  color: rgb(0, 108, 73);
  border-color: rgb(0, 108, 73);
  background: rgba(0, 108, 73, 0.04);
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
