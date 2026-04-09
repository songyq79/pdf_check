/**
 * LocalStorage封装工具
 */

const STORAGE_PREFIX = 'paper_check_'

/**
 * 存储数据到localStorage
 * @param {string} key - 键名
 * @param {any} value - 值（会自动JSON序列化）
 * @throws {Error} 当存储失败时抛出错误
 */
export function setStorage(key, value) {
  try {
    const serialized = JSON.stringify(value)
    localStorage.setItem(STORAGE_PREFIX + key, serialized)
    return true
  } catch (error) {
    console.error('存储数据失败:', error)
    // 抛出错误让调用方能够处理（如 localStorage 满了）
    throw error
  }
}

/**
 * 从localStorage获取数据
 * @param {string} key - 键名
 * @param {any} defaultValue - 默认值
 * @returns {any} - 解析后的值
 */
export function getStorage(key, defaultValue = null) {
  try {
    const item = localStorage.getItem(STORAGE_PREFIX + key)
    return item ? JSON.parse(item) : defaultValue
  } catch (error) {
    console.error('读取数据失败:', error)
    return defaultValue
  }
}

/**
 * 从localStorage删除数据
 * @param {string} key - 键名
 */
export function removeStorage(key) {
  try {
    localStorage.removeItem(STORAGE_PREFIX + key)
    return true
  } catch (error) {
    console.error('删除数据失败:', error)
    return false
  }
}

/**
 * 清空所有存储的数据
 */
export function clearStorage() {
  try {
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.startsWith(STORAGE_PREFIX)) {
        localStorage.removeItem(key)
      }
    })
    return true
  } catch (error) {
    console.error('清空数据失败:', error)
    return false
  }
}

/**
 * 获取存储数据的大小（字节）
 */
export function getStorageSize() {
  let size = 0
  const keys = Object.keys(localStorage)
  keys.forEach(key => {
    if (key.startsWith(STORAGE_PREFIX)) {
      size += localStorage.getItem(key).length
    }
  })
  return size
}
