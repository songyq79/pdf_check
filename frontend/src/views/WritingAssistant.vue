<template>
  <div class="page-container">
    <div class="page-title">高级写作辅助</div>
    <div class="page-description">
      把论文段落粘进来，AI 从语法、风格、逻辑、论证四个维度给出具体修改建议（按段检查，每段消耗 2 次额度）。建议供参考，最终修改由你决定。
    </div>

    <div class="wa-layout">
      <!-- 左：编辑器 -->
      <el-card class="wa-editor">
        <div class="wa-toolbar">
          <el-radio-group v-model="paperType" size="small">
            <el-radio-button value="humanities">人文社科</el-radio-button>
            <el-radio-button value="science_engineering">理工农医</el-radio-button>
            <el-radio-button value="arts">艺术</el-radio-button>
          </el-radio-group>
          <span class="wa-count">{{ paragraph.length }} 字</span>
        </div>
        <el-input
          v-model="paragraph"
          type="textarea"
          :rows="16"
          maxlength="2000"
          placeholder="粘贴或输入要检查的论文段落（单段，≤2000 字）..."
        />
        <div class="wa-submit">
          <CostHint action="writing_assist" />
          <el-button type="primary" :loading="loading" :disabled="!paragraph.trim()" @click="handleCheck">
            检查本段
          </el-button>
        </div>
      </el-card>

      <!-- 右：反馈面板 -->
      <el-card class="wa-panel">
        <div v-if="!result" class="wa-empty">
          <el-icon :size="40" color="#cbd5e1"><EditPen /></el-icon>
          <p>填写段落后点「检查本段」,这里显示四维建议</p>
        </div>
        <div v-else>
          <div class="wa-overall" v-if="result.overall">
            <strong>总评:</strong> {{ result.overall }}
            <span class="wa-issuecount">共 {{ result.issue_count }} 处建议</span>
          </div>
          <div v-if="result.issue_count === 0" class="wa-clean">✅ 未发现明显问题,写得不错!</div>

          <div v-for="dim in dims" :key="dim.key" v-show="result[dim.key]?.length">
            <div class="wa-dim-title" :style="{ color: dim.color }">{{ dim.label }}（{{ result[dim.key].length }}）</div>
            <div v-for="(item, i) in result[dim.key]" :key="i" class="wa-item">
              <div class="wa-excerpt">「{{ item.excerpt }}」</div>
              <div class="wa-issue">⚠ {{ item.issue }}</div>
              <div class="wa-suggestion">💡 {{ item.suggestion }}</div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { EditPen } from '@element-plus/icons-vue'
import writingAPI from '@/api/writingAssistant'
import CostHint from '@/components/common/CostHint.vue'

const paragraph = ref('')
const paperType = ref('humanities')
const loading = ref(false)
const result = ref(null)

const dims = [
  { key: 'grammar', label: '语法', color: '#dc2626' },
  { key: 'style', label: '风格', color: '#d97706' },
  { key: 'logic', label: '逻辑', color: '#2563eb' },
  { key: 'argument', label: '论证', color: '#7c3aed' },
]

async function handleCheck() {
  if (!paragraph.value.trim()) return
  loading.value = true
  try {
    result.value = await writingAPI.check(paragraph.value, paperType.value)
  } catch (e) {
    // 402/错误由全局拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.wa-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 900px) { .wa-layout { grid-template-columns: 1fr; } }

.wa-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.wa-count { font-size: 12px; color: rgb(156,163,175); }
.wa-submit { display: flex; align-items: center; justify-content: flex-end; gap: 16px; margin-top: 12px; }
.cost-hint { font-size: 13px; color: rgb(107,114,128); }
.cost-hint strong { color: #006C49; }

.wa-panel { min-height: 400px; }
.wa-empty { text-align: center; color: rgb(156,163,175); padding: 80px 20px; }
.wa-empty p { margin-top: 12px; font-size: 13px; }

.wa-overall { font-size: 14px; color: rgb(31,41,55); background: rgba(0,108,73,0.05); border-radius: 12px; padding: 12px; margin-bottom: 16px; }
.wa-issuecount { float: right; font-size: 12px; color: #006C49; }
.wa-clean { font-size: 14px; color: #008000; padding: 12px 0; }

.wa-dim-title { font-size: 14px; font-weight: 600; margin: 14px 0 8px; }
.wa-item { border-left: 3px solid #e5e7eb; padding: 6px 0 6px 12px; margin-bottom: 10px; }
.wa-excerpt { font-size: 13px; color: rgb(75,85,99); font-style: italic; margin-bottom: 4px; }
.wa-issue { font-size: 13px; color: #b45309; margin-bottom: 2px; }
.wa-suggestion { font-size: 13px; color: rgb(31,41,55); }

:deep(.el-card) { border-radius: 24px; border: 1px solid rgba(229,231,235,0.5); box-shadow: 0 4px 32px rgba(0,0,0,0.06); }
:deep(.el-button--primary) { background: rgb(0,108,73); border-color: rgb(0,108,73); border-radius: 9999px; }
:deep(.el-button--primary:hover) { background: rgb(0,90,60); border-color: rgb(0,90,60); }
:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: rgba(79,251,182,0.08); border-color: rgb(0,108,73) !important;
  color: rgb(0,108,73); box-shadow: -1px 0 0 0 rgb(0,108,73);
}
</style>
