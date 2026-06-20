import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/evaluation',
    name: 'Evaluation',
    component: () => import('@/views/Evaluation.vue'),
    meta: { title: '智能评价', requiresAuth: true }
  },
  {
    path: '/topic-evaluation',
    name: 'TopicEvaluation',
    component: () => import('@/views/TopicEvaluation.vue'),
    meta: { title: '选题评估', requiresAuth: true }
  },
  {
    path: '/spell-check',
    name: 'SpellCheck',
    component: () => import('@/views/SpellCheck.vue'),
    meta: { title: '错别字检查', requiresAuth: true }
  },
  {
    path: '/formatting',
    name: 'Formatting',
    component: () => import('@/views/Formatting.vue'),
    meta: { title: '模板排版', requiresAuth: true }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: { title: '历史记录', requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/auth/wechat/callback',
    name: 'WechatCallback',
    component: () => import('@/views/WechatCallback.vue'),
    meta: { title: '微信登录', requiresAuth: false }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin.vue'),
    meta: { title: '用户管理', requiresAuth: true }
  },
  {
    path: '/plagiarism',
    name: 'Plagiarism',
    component: () => import('@/views/Plagiarism.vue'),
    meta: { title: '论文查重', requiresAuth: true }
  },
  {
    path: '/pricing',
    name: 'Pricing',
    component: () => import('@/views/Pricing.vue'),
    meta: { title: '定价' }
  },
  {
    path: '/user-center',
    name: 'UserCenter',
    component: () => import('@/views/UserCenter.vue'),
    meta: { title: '用户中心', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '论文评价检验系统'} - 论文评价检验系统`

  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('access_token')
    if (!token) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
  }
  next()
})

export default router
