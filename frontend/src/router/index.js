import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: {
      title: '首页'
    }
  },
  {
    path: '/evaluation',
    name: 'Evaluation',
    component: () => import('@/views/Evaluation.vue'),
    meta: {
      title: '智能评价'
    }
  },
  {
    path: '/spell-check',
    name: 'SpellCheck',
    component: () => import('@/views/SpellCheck.vue'),
    meta: {
      title: '错别字检查'
    }
  },
  {
    path: '/formatting',
    name: 'Formatting',
    component: () => import('@/views/Formatting.vue'),
    meta: {
      title: '模板排版'
    }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: {
      title: '历史记录'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：设置页面标题
router.beforeEach((to, from, next) => {
  const title = to.meta.title || '论文评价检验系统'
  document.title = `${title} - 论文评价检验系统`
  next()
})

export default router
