import { createPinia } from 'pinia'

const pinia = createPinia()

// 添加持久化插件
pinia.use(({ store }) => {
  // 从 localStorage 恢复状态
  const savedState = localStorage.getItem(`pinia-${store.$id}`)
  if (savedState) {
    try {
      store.$patch(JSON.parse(savedState))
    } catch (e) {
      console.warn(`Failed to restore state for ${store.$id}:`, e)
    }
  }

  // 监听状态变化并保存到 localStorage
  store.$subscribe((mutation, state) => {
    try {
      // 过滤掉不需要持久化的字段
      const stateToPersist = { ...state }
      
      // 移除 pendingResult（这是临时状态，不需要持久化）
      delete stateToPersist.pendingResult
      
      localStorage.setItem(`pinia-${store.$id}`, JSON.stringify(stateToPersist))
    } catch (e) {
      console.warn(`Failed to persist state for ${store.$id}:`, e)
    }
  })
})

export default pinia
