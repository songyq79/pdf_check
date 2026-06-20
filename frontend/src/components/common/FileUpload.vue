<template>
  <div class="file-upload">
    <!-- 文件未选择时显示上传区域 -->
    <div
      v-if="!selectedFile"
      class="upload-area"
      :class="{ dragging: isDragging, disabled: disabled }"
      @click="handleClick"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
    >
      <el-icon class="upload-icon" :size="60">
        <UploadFilled />
      </el-icon>
      <div class="upload-text">
        <p class="upload-primary-text">
          {{ isDragging ? '释放文件以上传' : '点击或拖拽文件到此处上传' }}
        </p>
        <p class="upload-secondary-text">
          仅支持 {{ accept }} 格式，文件大小不超过 {{ maxSizeMB }}MB
        </p>
      </div>
    </div>

    <!-- 文件已选择时显示文件信息 -->
    <div v-else class="file-preview">
      <el-icon class="file-icon" :size="40">
        <Document />
      </el-icon>
      <div class="file-info">
        <div class="file-name">{{ selectedFile.name }}</div>
        <div class="file-meta">
          <span>{{ formatFileSize(selectedFile.size) }}</span>
          <span class="file-type">{{ getFileExtension(selectedFile.name) }}</span>
        </div>
      </div>
      <el-button
        v-if="!disabled"
        type="danger"
        :icon="Delete"
        circle
        @click="handleRemove"
      />
    </div>

    <!-- 上传进度条 -->
    <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
      <el-progress :percentage="uploadProgress" :status="uploadStatus" />
    </div>

    <!-- 隐藏的file input -->
    <input
      ref="fileInputRef"
      type="file"
      :accept="accept"
      style="display: none"
      @change="handleFileChange"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { UploadFilled, Document, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { validateFile, formatFileSize, getFileExtension } from '@/utils/fileUtils'

const props = defineProps({
  // 接受的文件类型
  accept: {
    type: String,
    default: '.docx'
  },
  // 最大文件大小（MB）
  maxSize: {
    type: Number,
    default: 20
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 上传进度（0-100）
  uploadProgress: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['file-selected', 'file-removed'])

// 状态
const fileInputRef = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)

// 计算属性
const maxSizeMB = computed(() => props.maxSize)
const uploadStatus = computed(() => {
  if (props.uploadProgress === 100) return 'success'
  return undefined
})

/**
 * 处理点击上传区域
 */
function handleClick() {
  if (props.disabled) return
  fileInputRef.value?.click()
}

/**
 * 处理文件选择
 */
function handleFileChange(event) {
  const file = event.target.files[0]
  if (file) {
    processFile(file)
  }
  // 清空input，允许重复选择同一文件
  event.target.value = ''
}

/**
 * 处理拖拽上传
 */
function handleDrop(event) {
  isDragging.value = false
  if (props.disabled) return

  const file = event.dataTransfer.files[0]
  if (file) {
    processFile(file)
  }
}

/**
 * 处理文件（验证并触发事件）
 */
function processFile(file) {
  // 验证文件
  const validation = validateFile(file, {
    maxSize: props.maxSize * 1024 * 1024,
    acceptedTypes: props.accept.split(',').map(t => t.trim())
  })

  if (!validation.valid) {
    ElMessage.error(validation.error)
    return
  }

  // 保存文件并触发事件
  selectedFile.value = file
  emit('file-selected', file)
}

/**
 * 移除文件
 */
function handleRemove() {
  selectedFile.value = null
  emit('file-removed')
}

/**
 * 暴露方法给父组件
 */
defineExpose({
  clearFile: handleRemove
})
</script>

<style scoped>
.file-upload {
  width: 100%;
}

.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #fff;
}

.upload-area:hover:not(.disabled) {
  border-color: rgb(0, 108, 73);
  background-color: rgba(79, 251, 182, 0.04);
}

.upload-area.dragging {
  border-color: rgb(0, 108, 73);
  background-color: rgba(79, 251, 182, 0.08);
}

.upload-area.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.upload-icon {
  color: rgb(0, 108, 73);
  margin-bottom: 20px;
}

.upload-text {
  color: rgb(107, 114, 128);
}

.upload-primary-text {
  font-size: 16px;
  margin-bottom: 8px;
}

.upload-secondary-text {
  font-size: 13px;
  color: rgb(107, 114, 128);
}

.file-preview {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background-color: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
}

.file-icon {
  color: rgb(0, 108, 73);
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 15px;
  font-weight: 500;
  color: rgb(18, 18, 18);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 5px;
}

.file-meta {
  font-size: 13px;
  color: rgb(107, 114, 128);
  display: flex;
  gap: 10px;
}

.file-type {
  text-transform: uppercase;
}

.upload-progress {
  margin-top: 15px;
}
</style>
