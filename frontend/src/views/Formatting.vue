<template>
  <div class="page-container">
    <div class="page-title">模板排版</div>
    <div class="page-description">
      选择标准学术论文模板，一键将文档字体、行距、标题层级统一调整为规范格式。
    </div>

    <!-- 空闲：选择模板 + 上传 -->
    <div v-if="store.isIdle">
      <el-card class="mb-20">
        <template #header>
          <div class="card-header">
            <el-icon><List /></el-icon>
            <span>选择排版模板</span>
          </div>
        </template>

        <div v-if="templatesLoading" class="loading-tip">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在加载模板列表...
        </div>

        <el-empty v-else-if="templates.length === 0" description="暂无可用模板" />

        <el-radio-group v-else v-model="selectedTemplateId" class="template-group">
          <el-radio
            v-for="t in templates"
            :key="t.id"
            :label="t.id"
            border
            class="template-radio"
          >
            <div class="template-option">
              <div class="template-name">{{ t.name }}</div>
              <div class="template-meta">
                <el-tag size="small" :type="categoryColor(t.category)">
                  {{ categoryLabel(t.category) }}
                </el-tag>
                <span class="template-school">{{ t.school_or_journal }}</span>
              </div>
              <div class="template-desc">{{ t.description }}</div>
            </div>
          </el-radio>
        </el-radio-group>
      </el-card>

      <FileUpload
        accept=".docx"
        :max-size="20"
        :disabled="!selectedTemplateId"
        @file-selected="handleFileSelected"
      />
      <div v-if="!selectedTemplateId" class="tip-text">请先选择模板，再上传文件</div>
    </div>

    <!-- 处理中 -->
    <div v-else-if="store.isProcessing">
      <el-card>
        <LoadingSpinner :size="60" :text="store.statusText" />
        <div class="mt-20">
          <el-progress :percentage="store.progress" :stroke-width="10" status="striped" striped-flow />
        </div>
        <div class="file-info mt-10">
          <el-icon><Document /></el-icon>
          <span>{{ store.currentFilename }}</span>
          <el-divider direction="vertical" />
          <el-icon><Stamp /></el-icon>
          <span>{{ store.selectedTemplateName }}</span>
        </div>
        <div class="mt-20" style="text-align:center;">
          <el-button @click="handleCancel">
            <el-icon><CircleClose /></el-icon>
            <span>取消排版</span>
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 完成 -->
    <div v-else-if="store.isCompleted">
      <!-- 降级模式警告 -->
      <el-alert
        v-if="store.warning"
        type="warning"
        :title="store.warning"
        :closable="false"
        show-icon
        class="mb-20"
      >
        <template #default>
          <div style="font-size: 13px; line-height: 1.6;">
            系统已自动从文档中提取文本内容进行排版，但可能丢失了部分格式、图片、表格等内容。
            <br>
            建议：在 Word 中打开文档，选择"另存为"，保存为新的 .docx 文件后重新上传。
          </div>
        </template>
      </el-alert>
      
      <el-card class="mb-20">
        <el-result
          icon="success"
          title="排版完成"
          :sub-title="`已应用模板：${store.selectedTemplateName}`"
        >
          <template #extra>
            <div class="result-meta">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="原文件">{{ store.currentFilename }}</el-descriptions-item>
                <el-descriptions-item label="模板">{{ store.selectedTemplateName }}</el-descriptions-item>
                <el-descriptions-item label="段落数">{{ store.formatResult.paragraphs }}</el-descriptions-item>
                <el-descriptions-item label="章节数">{{ store.formatResult.sections }}</el-descriptions-item>
                <el-descriptions-item label="样式应用">{{ store.formatResult.applied }} 处</el-descriptions-item>
                <el-descriptions-item label="耗时">{{ store.formatResult.time }}s</el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
        </el-result>
      </el-card>

      <el-alert title="格式化说明" type="success" :closable="false" show-icon class="mb-20">
        系统已按所选模板统一调整页面边距、字体、字号、行距及标题层级。下载后直接使用 Word 打开即可。
      </el-alert>

      <div class="button-group">
        <el-button size="large" @click="store.reset()">
          <el-icon><RefreshLeft /></el-icon>
          重新排版
        </el-button>
        <el-button type="success" size="large" @click="handleDownload">
          <el-icon><Download /></el-icon>
          下载排版文档
        </el-button>
      </div>
    </div>

    <!-- 失败 -->
    <div v-else-if="store.isFailed">
      <el-result icon="error" title="排版失败" :sub-title="store.errorMsg">
        <template #extra>
          <el-button type="primary" @click="store.reset()">重新上传</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import {
  List, Loading, Document, Stamp,
  RefreshLeft, Download, CircleClose,
} from '@element-plus/icons-vue'
import FileUpload from '@/components/common/FileUpload.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import formattingAPI from '@/api/formatting'
import { useFormattingStore } from '@/store/modules/formatting'
import { useHistoryStore } from '@/store/modules/history'

const store = useFormattingStore()
const historyStore = useHistoryStore()
const route = useRoute()

const templates = ref([])
const templatesLoading = ref(true)
const selectedTemplateId = ref(store.selectedTemplateId || '')

// 加载待展示结果或保持当前状态
onMounted(() => {
  loadTemplates()
  store.loadPendingOrKeep()
  store.resumeIfProcessing()
  
  // 若 store 中有模板选中记录则还原
  if (store.selectedTemplateId) {
    selectedTemplateId.value = store.selectedTemplateId
  }
  
  // 移除自动重置逻辑，用户需要主动点击"重新排版"按钮才会重置
  // 这样刷新页面、切换菜单后都能保持结果显示
})
onBeforeUnmount(() => store.stopPolling())

// 监听路由变化，当从其他页面返回时恢复状态
watch(() => route.path, (newPath) => {
  if (newPath === '/formatting') {
    // 如果是处理中状态，恢复轮询
    if (store.isProcessing) {
      store.resumeIfProcessing()
    }
  }
})

async function loadTemplates() {
  templatesLoading.value = true
  try {
    const res = await formattingAPI.getTemplates()
    templates.value = (res.templates || []).map(t => ({
      id: t.id,
      name: t.name,
      category: t.category,
      school_or_journal: t.school_or_journal,
      description: t.description,
    }))
    if (templates.value.length > 0 && !selectedTemplateId.value) {
      selectedTemplateId.value = templates.value[0].id
    }
  } catch {
    ElMessage.warning('模板列表加载失败，请刷新重试')
  } finally {
    templatesLoading.value = false
  }
}

async function handleFileSelected(file) {
  if (!selectedTemplateId.value) {
    ElMessage.warning('请先选择模板')
    return
  }

  const duplicate = historyStore.records.find(
    r => r.type === 'formatting' && r.result?.file_name === file.name
  )
  if (duplicate) {
    try {
      await ElMessageBox.confirm(
        `"${file.name}" 已有排版记录，重复上传将重新生成文档，是否继续？`,
        '重复文档',
        { confirmButtonText: '继续排版', cancelButtonText: '取消', type: 'warning' }
      )
    } catch {
      return
    }
  }

  const templateName = templates.value.find(t => t.id === selectedTemplateId.value)?.name || ''
  await store.uploadAndFormat(file, selectedTemplateId.value, templateName)
  if (store.isFailed) {
    ElMessage.error(store.errorMsg || '提交失败，请重试')
  }
}

function handleCancel() {
  store.cancel()
  ElMessage.info('已取消排版')
}

function handleDownload() {
  if (!store.currentTaskId) return
  formattingAPI.download(store.currentTaskId)
  ElMessage.success('开始下载排版文档')
}

function categoryLabel(cat) {
  return { universities: '高校', journals: '期刊', custom: '自定义' }[cat] ?? cat
}
function categoryColor(cat) {
  return { universities: 'primary', journals: 'success', custom: 'info' }[cat] ?? ''
}
</script>

<style scoped>
.template-group { display: flex; flex-direction: column; gap: 12px; width: 100%; }
.template-radio { width: 100%; height: auto; padding: 14px 16px; margin-right: 0 !important; }
.template-option { text-align: left; }
.template-name { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 6px; }
.template-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.template-school { font-size: 12px; color: #606266; }
.template-desc { font-size: 12px; color: #909399; line-height: 1.5; }
.card-header { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: bold; }
.loading-tip { display: flex; align-items: center; gap: 8px; color: #909399; padding: 20px 0; }
.tip-text { text-align: center; color: #909399; font-size: 13px; margin-top: 8px; }
.file-info { display: flex; align-items: center; gap: 6px; color: #909399; font-size: 13px; }
.result-meta { width: 100%; margin-top: 16px; }
.button-group { display: flex; gap: 12px; flex-wrap: wrap; }
.mt-10 { margin-top: 10px; }
.mt-20 { margin-top: 20px; }
.mb-20 { margin-bottom: 20px; }
</style>
