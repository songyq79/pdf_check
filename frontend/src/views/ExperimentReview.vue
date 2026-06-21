<template>
  <div class="page-container">
    <div class="page-title">实验设计评审</div>
    <div class="page-description">
      粘贴你的实验方案，AI 从科学性、完整性评分，对照「毁掉研究的结构性错误清单」（伪重复/混杂/批次效应等）排查，识别风险并给出方法论建议（理工科适用，消耗 3 次额度）。
    </div>

    <!-- 表单 -->
    <div v-if="state === 'form'">
      <el-card class="mb-20">
        <el-form :model="form" label-position="top">
          <el-form-item label="学科">
            <el-input v-model="form.discipline" placeholder="如：生物学 / 化学 / 材料科学 / 机械工程（选填）" />
          </el-form-item>
          <el-form-item label="实验方案" required>
            <el-input
              v-model="form.plan_text"
              type="textarea"
              :rows="14"
              maxlength="5000"
              show-word-limit
              placeholder="描述你的实验方案：研究对象、分组、变量、样本量、流程、对照、测量与统计方法..."
            />
          </el-form-item>
        </el-form>
        <div class="submit-bar">
          <CostHint action="experiment_evaluation" />
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">开始评审</el-button>
        </div>
      </el-card>
    </div>

    <!-- 处理 -->
    <div v-else-if="state === 'processing'">
      <el-card style="text-align:center; padding:40px 20px;">
        <el-icon class="spin" :size="48" color="#006C49"><Loading /></el-icon>
        <div style="margin:16px 0 8px; font-size:16px; font-weight:600;">{{ progressMsg }}</div>
        <div style="max-width:420px; margin:16px auto 0;">
          <el-progress :percentage="progress" :stroke-width="10" color="#006C49" />
        </div>
        <div class="mt-20"><el-button @click="handleReset">取消</el-button></div>
      </el-card>
    </div>

    <!-- 失败 -->
    <div v-else-if="state === 'failed'">
      <el-card>
        <el-result icon="error" title="评审失败" :sub-title="errorMsg || '请稍后重试'">
          <template #extra><el-button type="primary" @click="handleReset">重新填写</el-button></template>
        </el-result>
      </el-card>
    </div>

    <!-- 结果 -->
    <div v-else-if="state === 'result' && result">
      <div class="verdict-banner mb-20">
        <div class="verdict-score">{{ result.scores.overall }}<span> / 10</span></div>
        <div class="verdict-label">{{ result.scores.verdict }}</div>
      </div>

      <div class="score-grid mb-20">
        <el-card>
          <div class="dim-name">科学性</div>
          <div class="dim-score" :style="{ color: scoreColor(result.scores.scientific_validity) }">{{ result.scores.scientific_validity }}<span>/10</span></div>
          <div class="dim-analysis">{{ result.analysis.scientific_validity }}</div>
        </el-card>
        <el-card>
          <div class="dim-name">完整性</div>
          <div class="dim-score" :style="{ color: scoreColor(result.scores.completeness) }">{{ result.scores.completeness }}<span>/10</span></div>
          <div class="dim-analysis">{{ result.analysis.completeness }}</div>
        </el-card>
      </div>

      <el-card class="mb-20">
        <div class="block-title">🔬 结构性错误排查</div>
        <div v-if="result.detected_flaws.length">
          <div v-for="(f,i) in result.detected_flaws" :key="i" class="flaw-item">⚠ {{ f }}</div>
        </div>
        <div v-else class="clean-hint">✅ 未发现清单内的结构性错误（伪重复/混杂/批次/别名等）</div>
      </el-card>

      <el-card v-if="result.risks.length" class="mb-20">
        <div class="block-title">⚠️ 风险识别</div>
        <div v-for="(r,i) in result.risks" :key="i" class="risk-item">
          <el-tag :type="sevType(r.severity)" size="small" effect="plain">{{ sevLabel(r.severity) }}</el-tag>
          <span class="risk-text">{{ r.type }}：{{ r.description }}</span>
        </div>
      </el-card>

      <el-card class="mb-20">
        <div class="block-title">💰 成本估算 & 💡 改进建议</div>
        <p v-if="result.cost_estimate" class="prose"><strong>成本/时间：</strong>{{ result.cost_estimate }}</p>
        <ul><li v-for="(s,i) in result.methodology_suggestions" :key="i">{{ s }}</li></ul>
      </el-card>

      <div class="button-group">
        <el-button size="large" @click="handleReset"><el-icon><RefreshLeft /></el-icon><span>重新评审</span></el-button>
        <el-button type="success" size="large" :disabled="!result.report_id" @click="handleDownload"><el-icon><Download /></el-icon><span>下载报告</span></el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, RefreshLeft, Download } from '@element-plus/icons-vue'
import expAPI from '@/api/experimentEvaluation'
import CostHint from '@/components/common/CostHint.vue'

const state = ref('form')
const submitting = ref(false)
const progress = ref(0)
const progressMsg = ref('正在评审...')
const errorMsg = ref('')
const result = ref(null)
let pollTimer = null
let taskId = null

const form = ref({ plan_text: '', discipline: '' })

function scoreColor(v) {
  if (v >= 8) return '#008000'
  if (v >= 6) return '#0064c8'
  if (v >= 4) return '#ffa500'
  return '#ff0000'
}
function sevType(s) { return { high: 'danger', medium: 'warning', low: 'info' }[s] || 'warning' }
function sevLabel(s) { return { high: '高', medium: '中', low: '低' }[s] || '中' }

async function handleSubmit() {
  if (form.value.plan_text.trim().length < 30) {
    ElMessage.warning('请填写较详细的实验方案（≥30 字）')
    return
  }
  submitting.value = true
  try {
    const res = await expAPI.submit(form.value)
    taskId = res.task_id
    state.value = 'processing'
    progress.value = 10
    progressMsg.value = '任务已提交，正在评审...'
    startPolling()
  } catch (e) { /* 拦截器处理 */ } finally { submitting.value = false }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const s = await expAPI.getStatus(taskId)
      if (typeof s.progress === 'number') progress.value = s.progress
      if (s.status === 'completed') { stopPolling(); await fetchResult() }
      else if (s.status === 'failed') { stopPolling(); errorMsg.value = s.error || '评审失败'; state.value = 'failed' }
      else if (s.status === 'processing') progressMsg.value = '对照结构性错误清单评审中...'
    } catch (e) { /* 静默 */ }
  }, 2000)
}
function stopPolling() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } }

async function fetchResult() {
  try {
    result.value = await expAPI.getResult(taskId)
    state.value = 'result'
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) { errorMsg.value = e._userMessage || '获取结果失败'; state.value = 'failed' }
}

function handleDownload() {
  if (!result.value?.report_id) { ElMessage.warning('报告未生成'); return }
  expAPI.downloadReport(result.value.report_id)
  ElMessage.success('开始下载报告')
}
function handleReset() {
  stopPolling(); taskId = null; result.value = null; progress.value = 0; errorMsg.value = ''; state.value = 'form'
}
onBeforeUnmount(stopPolling)
</script>

<style scoped>
.submit-bar { display: flex; align-items: center; justify-content: flex-end; gap: 16px; margin-top: 8px; }
.cost-hint { font-size: 13px; color: rgb(107,114,128); }
.cost-hint strong { color: #006C49; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.verdict-banner { background: linear-gradient(135deg, #006C49, #00a86b); border-radius: 24px; padding: 28px; color: #fff; text-align: center; }
.verdict-score { font-size: 48px; font-weight: 700; }
.verdict-score span { font-size: 20px; opacity: .8; }
.verdict-label { font-size: 17px; font-weight: 600; margin-top: 4px; }

.score-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 700px) { .score-grid { grid-template-columns: 1fr; } }
.dim-name { font-size: 15px; font-weight: 600; margin-bottom: 8px; }
.dim-score { font-size: 32px; font-weight: 700; }
.dim-score span { font-size: 14px; color: rgb(107,114,128); margin-left: 2px; }
.dim-analysis { font-size: 13px; color: rgb(75,85,99); line-height: 1.6; margin-top: 10px; }

.block-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; }
.flaw-item { font-size: 14px; color: #b91c1c; line-height: 1.9; }
.clean-hint { font-size: 14px; color: #008000; }
.risk-item { display: flex; align-items: flex-start; gap: 8px; padding: 6px 0; }
.risk-text { font-size: 14px; color: rgb(55,65,81); }
.prose { font-size: 14px; line-height: 1.8; color: rgb(55,65,81); }
ul { padding-left: 20px; margin: 8px 0 0; }
ul li { font-size: 14px; line-height: 1.8; color: rgb(55,65,81); }
.button-group { display: flex; gap: 12px; justify-content: center; }

:deep(.el-card) { border-radius: 24px; border: 1px solid rgba(229,231,235,0.5); box-shadow: 0 4px 32px rgba(0,0,0,0.06); }
:deep(.el-button--primary) { background: rgb(0,108,73); border-color: rgb(0,108,73); border-radius: 9999px; }
:deep(.el-button--primary:hover) { background: rgb(0,90,60); border-color: rgb(0,90,60); }
</style>
