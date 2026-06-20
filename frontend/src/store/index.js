import { createPinia } from 'pinia'

const pinia = createPinia()

// 添加持久化插件
pinia.use(({ store }) => {
  console.log(`[Pinia] 初始化 store: ${store.$id}`)
  
  // 从 localStorage 恢复状态
  const savedState = localStorage.getItem(`pinia-${store.$id}`)
  if (savedState) {
    try {
      const parsed = JSON.parse(savedState)
      // 查重/任务进行中的状态不恢复，避免刷新后卡在检测中
      if (store.$id === 'plagiarism' && ['pending', 'processing', 'uploading', 'partial'].includes(parsed.status)) {
        parsed.status = 'idle'
        parsed.progress = 0
        parsed.taskId = ''
      }
      store.$patch(parsed)
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
