<template>
  <div id="app">
    <!-- 顶部导航栏 - 新设计 -->
    <header class="modern-header">
      <div class="header-container">
        <router-link to="/" class="logo">VRonly</router-link>

        <nav class="nav">
          <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
            首页
          </router-link>
          <router-link to="/evaluation" class="nav-item" :class="{ active: $route.path === '/evaluation' }">
            智能评价
          </router-link>
          <router-link to="/topic-evaluation" class="nav-item" :class="{ active: $route.path === '/topic-evaluation' }">
            选题评估
          </router-link>
          <router-link to="/literature-review" class="nav-item" :class="{ active: $route.path === '/literature-review' }">
            文献综述
          </router-link>
          <router-link to="/writing-assistant" class="nav-item" :class="{ active: $route.path === '/writing-assistant' }">
            写作辅助
          </router-link>
          <router-link to="/experiment-review" class="nav-item" :class="{ active: $route.path === '/experiment-review' }">
            实验评审
          </router-link>
          <router-link to="/spell-check" class="nav-item" :class="{ active: $route.path === '/spell-check' }">
            错别字检查
          </router-link>
          <router-link to="/formatting" class="nav-item" :class="{ active: $route.path === '/formatting' }">
            模板排版
          </router-link>
          <router-link to="/plagiarism" class="nav-item" :class="{ active: $route.path === '/plagiarism' }">
            论文查重
          </router-link>
        </nav>

        <!-- 登录状态区域 -->
        <div class="auth-area">
          <template v-if="authStore.isLoggedIn">
            <el-dropdown @command="handleUserCommand">
              <span class="user-info">
                <div class="user-avatar">
                  <div class="user-avatar-icon"></div>
                </div>
                <span class="user-name">{{ authStore.username }}</span>
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="user-center">用户中心</el-dropdown-item>
                  <el-dropdown-item command="history">历史记录</el-dropdown-item>
                  <el-dropdown-item command="pricing">购买套餐</el-dropdown-item>
                  <el-dropdown-item v-if="authStore.isAdmin" command="admin">管理后台</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <button class="login-btn" @click="router.push('/login')">登录 / 注册</button>
          </template>
        </div>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="main-content">
      <router-view v-slot="{ Component }" :key="$route.fullPath">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 页脚 -->
    <Footer />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import Footer from '@/components/common/Footer.vue'
import { useAuthStore } from '@/store/modules/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

let checkUserStatusInterval = null

// 应用启动时尝试恢复登录状态
onMounted(() => {
  authStore.fetchMe()

  // 每30秒检查一次用户状态，防止被拒绝用户仍能使用系统
  checkUserStatusInterval = setInterval(() => {
    if (authStore.isLoggedIn) {
      authStore.fetchMe()
    }
  }, 30000) // 30 秒检查一次
})

// 清理定时器
onUnmounted(() => {
  if (checkUserStatusInterval) {
    clearInterval(checkUserStatusInterval)
  }
})

function handleUserCommand(cmd) {
  if (cmd === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  } else if (cmd === 'admin') {
    router.push('/admin')
  } else if (cmd === 'user-center') {
    router.push('/user-center')
  } else if (cmd === 'history') {
    router.push('/history')
  } else if (cmd === 'pricing') {
    router.push('/pricing')
  }
}
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  margin-top: 80px;
}

/* 现代化导航栏 */
.modern-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  height: 80px;
  background: rgba(255, 255, 255, 0.70);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-container {
  width: 1000px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
}

/* Logo 样式 */
.logo {
  font-family: 'Newsreader', serif;
  font-size: 24px;
  font-weight: 400;
  font-style: italic;
  color: rgb(24, 24, 27);
  text-decoration: none;
  width: 90px;
  flex-shrink: 0;
}

/* 导航菜单 */
.nav {
  display: flex;
  align-items: center;
  gap: 32px;
}

.nav-item {
  font-size: 16px;
  color: rgb(26, 28, 28);
  text-decoration: none;
  font-family: 'PingFang SC', 'Noto Sans SC', sans-serif;
  line-height: 24px;
  padding-bottom: 3px;
  position: relative;
  font-weight: 400;
  transition: color 0.18s ease;
  white-space: nowrap;
}

.nav-item--muted {
  color: rgb(113, 113, 122);
}

.nav-item:hover {
  color: rgb(16, 185, 129);
}

.nav-item.active {
  border-bottom: 1px solid rgb(16, 185, 129);
  color: rgb(26, 28, 28);
  font-weight: 400;
}

/* 登录区域 */
.auth-area {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.login-btn {
  background: rgb(18, 18, 18);
  color: white;
  border: none;
  border-radius: 9999px;
  height: 36px;
  width: 92px;
  font-size: 16px;
  cursor: pointer;
  font-family: 'PingFang SC', 'Noto Sans SC', sans-serif;
  transition: opacity 0.18s ease;
}

.login-btn:hover {
  opacity: 0.85;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: rgb(26, 28, 28);
  font-size: 14px;
}

.user-info:hover {
  color: rgb(16, 185, 129);
}

.user-name {
  font-weight: 500;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 用户头像 */
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgb(18, 18, 18);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.user-avatar-icon {
  width: 32px;
  height: 32px;
  background: white;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

/* 头像人形图标 - 头部 */
.user-avatar-icon::before {
  content: '';
  position: absolute;
  top: 9px;
  width: 12px;
  height: 12px;
  background: rgb(18, 18, 18);
  border-radius: 50%;
}

/* 头像人形图标 - 身体 */
.user-avatar-icon::after {
  content: '';
  position: absolute;
  bottom: 7px;
  width: 20px;
  height: 14px;
  background: rgb(18, 18, 18);
  border-radius: 10px 10px 0 0;
}

/* 路由切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 1100px) {
  .header-container {
    width: calc(100% - 80px);
  }
}

@media (max-width: 680px) {
  .modern-header {
    height: 64px;
  }

  .header-container {
    height: 64px;
    width: calc(100% - 40px);
  }

  .main-content {
    margin-top: 64px;
  }

  .logo {
    font-size: 20px;
    width: auto;
  }

  .nav {
    gap: 16px;
  }

  .nav-item {
    font-size: 14px;
  }

  .login-btn {
    font-size: 14px;
    width: 80px;
  }
}
</style>
