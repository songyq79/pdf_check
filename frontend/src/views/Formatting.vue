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
            <div class="card-header-left">
              <el-icon><List /></el-icon>
              <span>选择排版模板</span>
            </div>
            <el-button type="primary" @click="showUploadDialog = true">
              <el-icon :size="18"><Upload /></el-icon>
              上传自定义模板
            </el-button>
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
              <div class="template-name-row">
                <span class="template-name">{{ t.name }}</span>
                <el-button
                  v-if="t.category === 'custom'"
                  type="danger"
                  size="small"
                  text
                  @click.stop="handleDeleteTemplate(t)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
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
      <div class="upload-tip">
        仅支持 .docx（排版需操作文档样式结构，PDF 不适用）
      </div>
      <div v-if="!selectedTemplateId" class="tip-text">请先选择模板，再上传文件</div>
      <div style="text-align:center; margin-top:12px;">
        <CostHint action="formatter" />
      </div>
    </div>

    <!-- 处理中 -->
    <div v-else-if="store.isProcessing">
      <el-card>
        <LoadingSpinner :size="60" :text="store.statusText" />
        <div class="mt-20">
          <el-progress :percentage="store.progress" :stroke-width="10" :show-text="false" />
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

    <!-- 上传自定义模板对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      :title="uploadStep === 'upload' ? '上传自定义模板' : '确认模板样式'"
      width="640px"
      :close-on-click-modal="false"
      @close="handleUploadDialogClose"
    >
      <!-- 第一步：上传 -->
      <div v-if="uploadStep === 'upload'">
        <el-form :model="uploadForm" label-width="90px">
          <el-form-item label="模板名称" required>
            <el-input
              v-model="uploadForm.name"
              placeholder="例如：XX大学2026毕业论文模板"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="模板描述">
            <el-input
              v-model="uploadForm.description"
              type="textarea"
              :rows="2"
              placeholder="简要描述模板的适用场景（选填）"
              maxlength="200"
            />
          </el-form-item>
          <el-form-item label="模板文件" required>
            <el-upload
              ref="templateUploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".docx"
              :on-change="handleTemplateFileChange"
              :on-remove="() => uploadForm.file = null"
              drag
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将 .docx 模板文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  请上传学校或期刊提供的标准模板文件（.docx格式），系统将自动提取其中的样式配置
                </div>
              </template>
            </el-upload>
          </el-form-item>
        </el-form>
      </div>

      <!-- 第二步：预览确认 -->
      <div v-else-if="uploadStep === 'preview'" class="preview-container">
        <!-- 验证警告 -->
        <el-alert
          v-if="analyzeResult.validation?.warnings?.length"
          type="warning"
          :closable="false"
          show-icon
          class="mb-16"
        >
          <template #title>
            <span>模板解析提示</span>
          </template>
          <template #default>
            <div v-for="(w, i) in analyzeResult.validation.warnings" :key="i" style="font-size:13px;">
              {{ w }}
            </div>
          </template>
        </el-alert>

        <!-- 页面设置 -->
        <div class="preview-card">
          <div class="preview-card-header">
            <el-icon :size="16" color="rgb(0, 108, 73)"><Document /></el-icon>
            <span>页面设置</span>
          </div>
          <div class="preview-tag-row">
            <el-tag size="large" effect="plain" type="primary">{{ formatPaperSize(analyzeResult.config?.page) }}</el-tag>
            <el-tag size="large" effect="plain">上 {{ formatMargin(analyzeResult.config?.page?.margin_top_cm) }}</el-tag>
            <el-tag size="large" effect="plain">下 {{ formatMargin(analyzeResult.config?.page?.margin_bottom_cm) }}</el-tag>
            <el-tag size="large" effect="plain">左 {{ formatMargin(analyzeResult.config?.page?.margin_left_cm) }}</el-tag>
            <el-tag size="large" effect="plain">右 {{ formatMargin(analyzeResult.config?.page?.margin_right_cm) }}</el-tag>
          </div>
        </div>

        <!-- 样式识别结果 -->
        <div class="preview-card">
          <div class="preview-card-header">
            <el-icon :size="16" color="#67C23A"><EditPen /></el-icon>
            <span>样式识别结果</span>
          </div>
          <el-table
            :data="styleTableData"
            :show-header="false"
            size="small"
            stripe
            class="style-table"
          >
            <el-table-column prop="label" width="100">
              <template #default="{ row }">
                <span class="style-table-label">{{ row.label }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="desc">
              <template #default="{ row }">
                <span class="style-table-desc">{{ row.desc }}</span>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="styleTableData.length === 0" class="preview-empty">
            未识别到标准样式
          </div>
        </div>

        <!-- 页眉页脚 -->
        <div v-if="analyzeResult.config?.header || analyzeResult.config?.footer" class="preview-card">
          <div class="preview-card-header">
            <el-icon :size="16" color="#E6A23C"><Memo /></el-icon>
            <span>页眉页脚</span>
          </div>
          <div class="preview-tag-row">
            <el-tag v-if="analyzeResult.config?.header" size="large" effect="plain" type="info">
              页眉：{{ analyzeResult.config.header.text || '（无文字）' }}
            </el-tag>
            <el-tag v-if="analyzeResult.config?.footer" size="large" effect="plain" type="info">
              页脚：{{ analyzeResult.config.footer.page_number ? '包含页码' : (analyzeResult.config.footer.text || '（无）') }}
            </el-tag>
          </div>
        </div>
      </div>

      <template #footer>
        <div v-if="uploadStep === 'upload'">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button
            type="primary"
            :loading="analyzing"
            :disabled="!uploadForm.name || !uploadForm.file"
            @click="handleAnalyzeTemplate"
          >
            解析模板
          </el-button>
        </div>
        <div v-else-if="uploadStep === 'preview'">
          <el-button @click="handleCancelAnalyze">返回修改</el-button>
          <el-button
            type="success"
            :loading="confirming"
            @click="handleConfirmTemplate"
          >
            确认保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import {
  List, Loading, Document, Stamp,
  RefreshLeft, Download, CircleClose,
  Upload, Delete, UploadFilled, EditPen, Memo,
} from '@element-plus/icons-vue'
import FileUpload from '@/components/common/FileUpload.vue'
import CostHint from '@/components/common/CostHint.vue'
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

// ── 上传自定义模板相关 ──
const showUploadDialog = ref(false)
const uploadStep = ref('upload') // 'upload' | 'preview'
const analyzing = ref(false)
const confirming = ref(false)
const templateUploadRef = ref(null)
const uploadForm = ref({
  name: '',
  description: '',
  file: null,
})
const analyzeResult = ref({
  temp_id: '',
  validation: {},
  config: {},
  style_summary: {},
})

onMounted(() => {
  loadTemplates()
  
  // 检查是否从历史记录页面跳转过来
  const fromHistory = route.query.from === 'history'
  
  // 如果有 pendingResult，说明是从历史记录跳转过来的，加载结果
  if (store.pendingResult) {
    store.loadPendingOrKeep()
    // 若 store 中有模板选中记录则还原
    if (store.selectedTemplateId) {
      selectedTemplateId.value = store.selectedTemplateId
    }
  }
  // 如果没有 pendingResult，但是状态是 completed，且不是从历史记录来的，需要重置
  else if (store.isCompleted && !fromHistory) {
    store.reset()
  }
  // 其他情况（idle、processing、failed 或从历史记录刷新）保持当前状态
  else {
    // 还原模板选择（如果有的话）
    if (store.selectedTemplateId) {
      selectedTemplateId.value = store.selectedTemplateId
    }
  }
  
  // 如果正在处理中，恢复轮询
  store.resumeIfProcessing()
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
  try {
    await store.uploadAndFormat(file, selectedTemplateId.value, templateName)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (err) {
    if (err?.response?.status !== 402) {
      ElMessage.error(store.errorMsg || '提交失败，请重试')
    }
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

// ── 预览格式化辅助函数 ──

function formatPaperSize(page) {
  if (!page) return ''
  const w = page.width_cm, h = page.height_cm
  const isA4 = Math.abs(w - 21.0) < 0.5 && Math.abs(h - 29.7) < 0.5
  return isA4 ? 'A4' : `${w?.toFixed(1)} × ${h?.toFixed(1)} cm`
}

function formatMargin(val) {
  if (val == null) return ''
  const rounded = Math.round(val * 10) / 10
  return rounded === Math.floor(rounded) ? `${Math.floor(rounded)} cm` : `${rounded} cm`
}

// 过滤掉样式摘要中的"页面设置"，转为 el-table 数据格式
const styleTableData = computed(() => {
  const raw = analyzeResult.value.style_summary || {}
  const rows = []
  for (const [label, desc] of Object.entries(raw)) {
    if (label !== '页面设置') rows.push({ label, desc })
  }
  return rows
})

// ── 上传自定义模板逻辑 ──

function handleTemplateFileChange(uploadFile) {
  uploadForm.value.file = uploadFile.raw
}

async function handleAnalyzeTemplate() {
  if (!uploadForm.value.name?.trim()) {
    ElMessage.warning('请填写模板名称')
    return
  }
  if (!uploadForm.value.file) {
    ElMessage.warning('请上传模板文件')
    return
  }

  analyzing.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('name', uploadForm.value.name.trim())
    formData.append('description', uploadForm.value.description || '')

    const res = await formattingAPI.analyzeTemplate(formData)
    analyzeResult.value = res
    uploadStep.value = 'preview'
  } catch (err) {
    ElMessage.error(err.message || '模板解析失败，请检查文件格式')
  } finally {
    analyzing.value = false
  }
}

async function handleConfirmTemplate() {
  confirming.value = true
  try {
    await formattingAPI.confirmTemplate({
      temp_id: analyzeResult.value.temp_id,
      name: uploadForm.value.name.trim(),
      description: uploadForm.value.description || '',
    })
    ElMessage.success('模板保存成功')
    showUploadDialog.value = false
    resetUploadForm()
    // 刷新模板列表
    await loadTemplates()
  } catch (err) {
    ElMessage.error(err.message || '模板保存失败')
  } finally {
    confirming.value = false
  }
}

function handleCancelAnalyze() {
  // 返回上传步骤，清理临时文件
  if (analyzeResult.value.temp_id) {
    formattingAPI.cancelTemplate(analyzeResult.value.temp_id).catch(() => {})
  }
  uploadStep.value = 'upload'
  analyzeResult.value = { temp_id: '', validation: {}, config: {}, style_summary: {} }
}

function handleUploadDialogClose() {
  // 关闭弹窗时清理
  if (uploadStep.value === 'preview' && analyzeResult.value.temp_id) {
    formattingAPI.cancelTemplate(analyzeResult.value.temp_id).catch(() => {})
  }
  resetUploadForm()
}

function resetUploadForm() {
  uploadStep.value = 'upload'
  uploadForm.value = { name: '', description: '', file: null }
  analyzeResult.value = { temp_id: '', validation: {}, config: {}, style_summary: {} }
  if (templateUploadRef.value) {
    templateUploadRef.value.clearFiles()
  }
}

async function handleDeleteTemplate(template) {
  try {
    await ElMessageBox.confirm(
      `确定要删除自定义模板"${template.name}"吗？删除后不可恢复。`,
      '删除模板',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  try {
    await formattingAPI.deleteTemplate(template.id)
    ElMessage.success('模板已删除')
    // 如果删除的是当前选中的模板，清空选择
    if (selectedTemplateId.value === template.id) {
      selectedTemplateId.value = ''
    }
    await loadTemplates()
  } catch (err) {
    ElMessage.error(err.message || '删除失败')
  }
}
</script>

<style scoped>
.template-group { display: flex; flex-direction: column; gap: 12px; width: 100%; }
.template-radio { width: 100%; height: auto; padding: 14px 16px; margin-right: 0 !important; }
:deep(.template-radio .el-radio__label) { white-space: normal !important; overflow: visible; text-overflow: unset; display: block; }
:deep(.template-radio.el-radio) { height: auto; align-items: flex-start; }
:deep(.template-radio .el-radio__input) { margin-top: 3px; flex-shrink: 0; }
.template-option { text-align: left; }
.template-name-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.template-name { font-size: 15px; font-weight: 600; color: rgb(18, 18, 18); }
.template-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.template-school { font-size: 12px; color: rgb(107, 114, 128); }
.template-desc { font-size: 12px; color: rgb(107, 114, 128); line-height: 1.5; white-space: normal; word-break: break-word; }
.card-header { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.card-header-left { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: bold; }
.loading-tip { display: flex; align-items: center; gap: 8px; color: rgb(107, 114, 128); padding: 20px 0; }
.tip-text { text-align: center; color: rgb(107, 114, 128); font-size: 13px; margin-top: 8px; }
.upload-tip { text-align: center; color: rgb(107, 114, 128); font-size: 13px; margin-top: 12px; }
.file-info { display: flex; align-items: center; gap: 6px; color: rgb(107, 114, 128); font-size: 13px; }
.result-meta { width: 100%; margin-top: 16px; }
.button-group { display: flex; gap: 12px; flex-wrap: wrap; }
.mt-10 { margin-top: 10px; }
.mt-20 { margin-top: 20px; }
.mb-16 { margin-bottom: 16px; }
.mb-20 { margin-bottom: 20px; }

/* ── 模板预览确认样式 ── */
.preview-container { display: flex; flex-direction: column; gap: 16px; }
.preview-card {
  background: rgb(249, 249, 249);
  border: 1px solid rgba(229, 231, 235, 0.50);
  border-radius: 16px;
  padding: 16px;
}
.preview-card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: rgb(18, 18, 18);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(229, 231, 235, 0.50);
}
.preview-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.preview-tag-row .el-tag { font-size: 13px; }
.preview-empty {
  color: rgb(107, 114, 128);
  font-size: 13px;
  text-align: center;
  padding: 12px 0;
}

/* 样式表格 */
.style-table { border-radius: 12px; overflow: hidden; }
.style-table-label {
  font-weight: 600;
  color: rgb(18, 18, 18);
  font-size: 14px;
}
.style-table-desc {
  color: rgb(107, 114, 128);
  font-size: 14px;
}

:deep(.el-card) {
  border-radius: 24px;
  border: 1px solid rgba(229, 231, 235, 0.50);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
}

:deep(.el-button--primary) {
  background: rgb(0, 108, 73);
  border-color: rgb(0, 108, 73);
  border-radius: 9999px;
}

:deep(.el-button--primary:hover) {
  background: rgb(0, 90, 60);
  border-color: rgb(0, 90, 60);
}
</style>
