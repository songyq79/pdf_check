<template>
  <div id="app">
    <!-- 顶部导航栏 - 新设计 -->
    <header class="modern-header">
      <div class="header-container">
        <div class="logo">
          <span class="logo-text">
            <span class="logo-vr">VR</span><span class="logo-only">only</span>
          </span>
          <span class="logo-subtitle">论文评价检验系统</span>
        </div>
        
        <nav class="nav">
          <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
            首页
          </router-link>
          <router-link to="/evaluation" class="nav-item" :class="{ active: $route.path === '/evaluation' }">
            智能评价
          </router-link>
          <router-link to="/spell-check" class="nav-item" :class="{ active: $route.path === '/spell-check' }">
            错别字检查
          </router-link>
          <router-link to="/formatting" class="nav-item" :class="{ active: $route.path === '/formatting' }">
            模板排版
          </router-link>
          <router-link to="/history" class="nav-item" :class="{ active: $route.path === '/history' }">
            历史记录
          </router-link>
          
          <div class="user-avatar">
            <div class="user-avatar-icon"></div>
          </div>
        </nav>
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
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Footer from '@/components/common/Footer.vue'

const route = useRoute()

// 当前激活的菜单项
const activeMenu = computed(() => route.path)
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
}

/* 现代化导航栏 */
.modern-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 70px;
}

/* Logo 样式 */
.logo {
  display: flex;
  align-items: center;
  gap: 15px;
}

.logo-text {
  font-family: 'Arial', sans-serif;
  font-size: 36px;
  font-weight: 700;
  letter-spacing: -1px;
  line-height: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-vr {
  font-weight: 700;
}

.logo-only {
  font-weight: 700;
}

.logo-subtitle {
  font-size: 16px;
  color: #666;
  font-weight: 500;
}

/* 导航菜单 */
.nav {
  display: flex;
  gap: 30px;
  align-items: center;
}

.nav-item {
  color: #666;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
  padding: 8px 0;
  position: relative;
}

.nav-item::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
}

.nav-item:hover {
  color: #667eea;
}

.nav-item:hover::after,
.nav-item.active::after {
  width: 100%;
}

.nav-item.active {
  color: #667eea;
  font-weight: 600;
}

/* 用户头像 */
.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  position: relative;
}

.user-avatar-icon {
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

/* 头部 */
.user-avatar-icon::before {
  content: '';
  position: absolute;
  top: 11px;
  width: 14px;
  height: 14px;
  background: #667eea;
  border-radius: 50%;
}

/* 身体 */
.user-avatar-icon::after {
  content: '';
  position: absolute;
  bottom: 8px;
  width: 24px;
  height: 16px;
  background: #667eea;
  border-radius: 12px 12px 0 0;
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
@media (max-width: 768px) {
  .header-container {
    padding: 0 15px;
    height: 60px;
  }

  .logo-text {
    font-size: 28px;
  }

  .logo-subtitle {
    font-size: 14px;
  }

  .nav {
    gap: 15px;
  }

  .nav-item {
    font-size: 14px;
  }

  .user-avatar {
    width: 38px;
    height: 38px;
  }

  .user-avatar-icon {
    width: 34px;
    height: 34px;
  }
}

@media (max-width: 480px) {
  .logo-subtitle {
    display: none;
  }

  .nav {
    gap: 10px;
  }

  .nav-item {
    font-size: 13px;
  }
}
</style>
