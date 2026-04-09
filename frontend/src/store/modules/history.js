import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getStorage, setStorage } from '@/utils/storage'

const HISTORY_KEY = 'evaluation_history'
const MAX_RECORDS = 100 // 最多保存100条记录，防止 localStorage 溢出

/**
 * 历史记录管理
 * 使用localStorage持久化
 */
export const useHistoryStore = defineStore('history', () => {
  // 状态
  const records = ref([])

  // 计算属性
  const hasRecords = computed(() => records.value.length > 0)
  const recordCount = computed(() => records.value.length)

  /**
   * 最近的记录（前5条）
   */
  const recentRecords = computed(() => {
    return records.value.slice(0, 5)
  })

  /**
   * 按类型筛选记录
   * @param {string} type - 记录类型
   */
  function getRecordsByType(type) {
    return records.value.filter(record => record.type === type)
  }

  /**
   * 按日期范围筛选记录
   * @param {number} startDate - 开始时间戳
   * @param {number} endDate - 结束时间戳
   */
  function getRecordsByDateRange(startDate, endDate) {
    return records.value.filter(
      record => record.timestamp >= startDate && record.timestamp <= endDate
    )
  }

  /**
   * 添加记录
   * @param {Object} record - 记录对象
   */
  function addRecord(record) {
    const newRecord = {
      id: Date.now().toString(),
      ...record
    }
    records.value.unshift(newRecord) // 添加到开头
    
    // 限制记录数量，防止 localStorage 溢出
    if (records.value.length > MAX_RECORDS) {
      records.value = records.value.slice(0, MAX_RECORDS)
    }
    
    saveToLocalStorage()
  }

  /**
   * 删除记录
   * @param {string} id - 记录ID
   */
  function deleteRecord(id) {
    const index = records.value.findIndex(record => record.id === id)
    if (index !== -1) {
      records.value.splice(index, 1)
      saveToLocalStorage()
    }
  }

  /**
   * 清空所有记录
   */
  function clearAllRecords() {
    records.value = []
    saveToLocalStorage()
  }

  /**
   * 保存到localStorage
   */
  function saveToLocalStorage() {
    try {
      setStorage(HISTORY_KEY, records.value)
    } catch (err) {
      console.error('[history] localStorage 保存失败:', err)
      // 如果保存失败（可能是空间不足），尝试删除旧记录后重试
      if (records.value.length > 50) {
        records.value = records.value.slice(0, 50)
        try {
          setStorage(HISTORY_KEY, records.value)
        } catch {
          console.error('[history] 清理后仍无法保存，localStorage 可能已满')
        }
      }
    }
  }

  /**
   * 从localStorage加载
   */
  function loadFromLocalStorage() {
    try {
      const stored = getStorage(HISTORY_KEY, [])
      // 限制加载的记录数量
      records.value = stored.slice(0, MAX_RECORDS)
    } catch (err) {
      console.error('[history] localStorage 加载失败:', err)
      records.value = []
    }
  }

  /**
   * 获取单条记录
   * @param {string} id - 记录ID
   */
  function getRecordById(id) {
    return records.value.find(record => record.id === id)
  }

  // 初始化时从localStorage加载
  loadFromLocalStorage()

  return {
    // 状态
    records,
    // 计算属性
    hasRecords,
    recordCount,
    recentRecords,
    // 方法
    addRecord,
    deleteRecord,
    clearAllRecords,
    getRecordsByType,
    getRecordsByDateRange,
    getRecordById,
    loadFromLocalStorage,
    saveToLocalStorage
  }
})
