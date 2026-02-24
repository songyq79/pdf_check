<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <el-menu
      :default-active="activeMenu"
      mode="horizontal"
      :ellipsis="false"
      background-color="#409EFF"
      text-color="#fff"
      active-text-color="#ffd04b"
      router
    >
      <el-menu-item index="/" style="font-size: 18px; font-weight: bold;">
        <el-icon><Reading /></el-icon>
        <span style="margin-left: 8px;">论文评价检验系统</span>
      </el-menu-item>

      <div class="flex-grow" />

      <el-menu-item index="/">
        <el-icon><HomeFilled /></el-icon>
        <span>首页</span>
      </el-menu-item>

      <el-menu-item index="/evaluation">
        <el-icon><Edit /></el-icon>
        <span>智能评价</span>
      </el-menu-item>

      <el-menu-item index="/spell-check">
        <el-icon><DocumentChecked /></el-icon>
        <span>错别字检查</span>
      </el-menu-item>

      <el-menu-item index="/formatting">
        <el-icon><Document /></el-icon>
        <span>模板排版</span>
      </el-menu-item>

      <el-menu-item index="/history">
        <el-icon><Clock /></el-icon>
        <span>历史记录</span>
      </el-menu-item>
    </el-menu>

    <!-- 主内容区域 -->
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 当前激活的菜单项
const activeMenu = computed(() => route.path)
</script>

<style scoped>
#app {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.flex-grow {
  flex-grow: 1;
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
</style>
