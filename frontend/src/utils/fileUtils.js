/**
 * 文件验证工具
 */

/**
 * 验证文件类型和大小
 * @param {File} file - 要验证的文件
 * @param {Object} options - 验证选项
 * @returns {Object} - { valid: boolean, error?: string }
 */
export function validateFile(file, options = {}) {
  const {
    acceptedTypes = ['.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    maxSize = 20 * 1024 * 1024 // 20MB
  } = options

  // 检查文件类型
  const isValidType = acceptedTypes.some(type => {
    if (type.startsWith('.')) {
      return file.name.toLowerCase().endsWith(type.toLowerCase())
    }
    return file.type === type
  })

  if (!isValidType) {
    return {
      valid: false,
      error: '仅支持 .docx 格式的文件'
    }
  }

  // 检查文件大小
  if (file.size > maxSize) {
    const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(0)
    return {
      valid: false,
      error: `文件大小不能超过 ${maxSizeMB}MB`
    }
  }

  return { valid: true }
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} - 格式化后的文件大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 获取文件扩展名
 * @param {string} filename - 文件名
 * @returns {string} - 扩展名（含.）
 */
export function getFileExtension(filename) {
  const lastDot = filename.lastIndexOf('.')
  return lastDot === -1 ? '' : filename.substring(lastDot)
}
