<template>
  <div class="page-container">
    <div class="page-title">选题评估</div>
    <div class="page-description">
      填写你的研究选题，AI 将检索真实相关文献，从创新性、可行性、重要性三个维度评估，并给出改进建议与相关文献（消耗 3 次额度）。
    </div>

    <!-- 表单状态 -->
    <div v-if="state === 'form'">
      <el-card class="mb-20">
        <el-form :model="form" label-position="top">
          <el-form-item label="拟研究问题" required>
            <el-input
              v-model="form.question"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
              placeholder="一句话描述你打算研究的核心问题"
            />
          </el-form-item>
          <el-form-item label="研究方向描述">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="4"
              maxlength="1000"
              show-word-limit
              placeholder="研究背景、拟采用的方法、预期目标等（选填）"
            />
          </el-form-item>
          <div class="form-row">
            <el-form-item label="学科" class="form-col">
              <el-input v-model="form.discipline" placeholder="如：计算机科学 / 中国语言文学" />
            </el-form-item>
            <el-form-item label="学位阶段" class="form-col">
              <el-select v-model="form.degree_level" placeholder="请选择" style="width:100%">
                <el-option label="本科" value="本科" />
                <el-option label="硕士" value="硕士" />
                <el-option label="博士" value="博士" />
              </el-select>
            </el-form-item>
          </div>

          <el-form-item label="论文类别">
            <el-radio-group v-model="form.paper_type" class="type-group">
              <el-radio-button value="humanities">人文社科类</el-radio-button>
              <el-radio-button value="science_engineering">理工农医类</el-radio-button>
              <el-radio-button value="arts">艺术类</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-form>

        <div class="submit-bar">
          <CostHint action="topic_evaluation" />
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
            开始评估
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 处理状态 -->
    <div v-else-if="state === 'processing'">
      <el-card style="text-align:center; padding:40px 20px;">
        <el-icon class="spin" :size="48" color="#006C49"><Loading /></el-icon>
        <div style="margin:16px 0 8px; font-size:16px; font-weight:600;">{{ progressMsg }}</div>
        <div style="max-width:420px; margin:16px auto 0;">
          <el-progress :percentage="progress" :stroke-width="10" color="#006C49" />
        </div>
        <div class="mt-20">
          <el-button @click="handleReset">取消</el-button>
        </div>
      </el-card>
    </div>

    <!-- 失败状态 -->
    <div v-else-if="state === 'failed'">
      <el-card>
        <el-result icon="error" title="评估失败" :sub-title="errorMsg || '请稍后重试'">
          <template #extra>
            <el-button type="primary" @click="handleReset">重新填写</el-button>
          </template>
        </el-result>
      </el-card>
    </div>

    <!-- 结果状态 -->
    <div v-else-if="state === 'result' && result">
      <!-- 综合结论 -->
      <div class="verdict-banner mb-20">
        <div class="verdict-score">{{ result.scores.overall }}<span> / 10</span></div>
        <div class="verdict-label">{{ result.scores.verdict }}</div>
        <div class="verdict-topic">{{ result.topic.question }}</div>
      </div>

      <!-- 三维评分 -->
      <div class="score-grid mb-20">
        <el-card v-for="dim in scoreDims" :key="dim.key">
          <div class="dim-name">{{ dim.label }}</div>
          <div class="dim-score" :style="{ color: scoreColor(dim.value) }">{{ dim.value }}<span>/10</span></div>
          <el-progress :percentage="dim.value * 10" :stroke-width="6" :color="scoreColor(dim.value)" :show-text="false" />
          <div class="dim-analysis">{{ dim.analysis }}</div>
        </el-card>
      </div>

      <!-- 亮点 / 挑战 / 建议 -->
      <div class="card-grid mb-20">
        <el-card v-if="result.key_novelties.length">
          <div class="block-title">✨ 核心创新点</div>
          <ul><li v-for="(x,i) in result.key_novelties" :key="i">{{ x }}</li></ul>
        </el-card>
        <el-card v-if="result.technical_challenges.length">
          <div class="block-title">⚠️ 技术难点 / 挑战</div>
          <ul><li v-for="(x,i) in result.technical_challenges" :key="i">{{ x }}</li></ul>
        </el-card>
      </div>

      <el-card v-if="result.improvement_suggestions.length" class="mb-20">
        <div class="block-title">💡 改进建议</div>
        <ul><li v-for="(x,i) in result.improvement_suggestions" :key="i">{{ x }}</li></ul>
      </el-card>

      <!-- 相关文献 -->
      <el-card class="mb-20">
        <div class="block-title">📚 相关文献（{{ result.related_papers.length }}）</div>
        <div v-if="result.related_papers.length">
          <div v-for="(p,i) in result.related_papers" :key="i" class="paper-item">
            <span class="paper-idx">[{{ i + 1 }}]</span>
            <span class="paper-title">{{ p.title }}</span>
            <span class="paper-meta">{{ (p.authors || []).slice(0,3).join(', ') }} · {{ p.year || '—' }}</span>
          </div>
        </div>
        <div v-else class="empty-hint">未检索到直接相关文献，评估基于学科常识，建议人工补充检索。</div>
      </el-card>

      <!-- 操作 -->
      <div class="button-group">
        <el-button size="large" @click="handleReset">
          <el-icon><RefreshLeft /></el-icon><span>重新评估</span>
        </el-button>
        <el-button type="success" size="large" :disabled="!result.report_id" @click="handleDownload">
          <el-icon><Download /></el-icon><span>下载报告</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, RefreshLeft, Download } from '@element-plus/icons-vue'
import topicAPI from '@/api/topicEvaluation'
import CostHint from '@/components/common/CostHint.vue'

const state = ref('form')          // form | processing | failed | result
const submitting = ref(false)
const progress = ref(0)
const progressMsg = ref('正在评估...')
const errorMsg = ref('')
const result = ref(null)

let pollTimer = null
let taskId = null

const form = ref({
  question: '',
  description: '',
  discipline: '',
  degree_level: '',
  paper_type: 'humanities',
})

const scoreDims = ref([])

function scoreColor(v) {
  if (v >= 8) return '#008000'
  if (v >= 6) return '#0064c8'
  if (v >= 4) return '#ffa500'
  return '#ff0000'
}

async function handleSubmit() {
  if (!form.value.question.trim()) {
    ElMessage.warning('请填写拟研究问题')
    return
  }
  submitting.value = true
  try {
    const res = await topicAPI.submit(form.value)
    taskId = res.task_id
    state.value = 'processing'
    progress.value = 5
    progressMsg.value = '任务已提交，正在解析选题...'
    startPolling()
  } catch (e) {
    // 402 由全局拦截器处理；其余静默（拦截器已弹）
  } finally {
    submitting.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const s = await topicAPI.getStatus(taskId)
      if (typeof s.progress === 'number') progress.value = s.progress
      if (s.status === 'completed') {
        stopPolling()
        await fetchResult()
      } else if (s.status === 'failed') {
        stopPolling()
        errorMsg.value = s.error || '评估失败'
        state.value = 'failed'
      } else if (s.status === 'processing') {
        progressMsg.value = '正在检索文献并生成评估...'
      }
    } catch (e) {
      // 轮询错误静默，下次重试
    }
  }, 2000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function fetchResult() {
  try {
    const r = await topicAPI.getResult(taskId)
    result.value = r
    scoreDims.value = [
      { key: 'innovation', label: '创新性', value: r.scores.innovation, analysis: r.analysis.innovation },
      { key: 'feasibility', label: '可行性', value: r.scores.feasibility, analysis: r.analysis.feasibility },
      { key: 'importance', label: '重要性', value: r.scores.importance, analysis: r.analysis.importance },
    ]
    state.value = 'result'
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    errorMsg.value = e._userMessage || '获取结果失败'
    state.value = 'failed'
  }
}

function handleDownload() {
  if (!result.value?.report_id) {
    ElMessage.warning('报告未生成')
    return
  }
  topicAPI.downloadReport(result.value.report_id)
  ElMessage.success('开始下载报告')
}

function handleReset() {
  stopPolling()
  taskId = null
  result.value = null
  progress.value = 0
  errorMsg.value = ''
  state.value = 'form'
}

onBeforeUnmount(stopPolling)
</script>

<style scoped>
.form-row { display: flex; gap: 16px; }
.form-col { flex: 1; }
.type-group { display: flex; gap: 8px; flex-wrap: wrap; }
.submit-bar { display: flex; align-items: center; justify-content: flex-end; gap: 16px; margin-top: 8px; }
.cost-hint { font-size: 13px; color: rgb(107,114,128); }
.cost-hint strong { color: #006C49; }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.verdict-banner {
  background: linear-gradient(135deg, #006C49, #00a86b);
  border-radius: 24px; padding: 32px; color: #fff; text-align: center;
}
.verdict-score { font-size: 56px; font-weight: 700; }
.verdict-score span { font-size: 22px; opacity: .8; }
.verdict-label { font-size: 18px; font-weight: 600; margin: 4px 0 12px; }
.verdict-topic { font-size: 14px; opacity: .9; }

.score-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.dim-name { font-size: 15px; font-weight: 600; margin-bottom: 8px; }
.dim-score { font-size: 32px; font-weight: 700; margin-bottom: 8px; }
.dim-score span { font-size: 14px; color: rgb(107,114,128); margin-left: 2px; }
.dim-analysis { font-size: 13px; color: rgb(75,85,99); line-height: 1.6; margin-top: 10px; }

.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.block-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; }
.card-grid ul, .block-title + ul { padding-left: 20px; margin: 0; }
ul li { font-size: 14px; line-height: 1.8; color: rgb(55,65,81); }

.paper-item { padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,.05); font-size: 13px; }
.paper-idx { color: #006C49; font-weight: 600; margin-right: 6px; }
.paper-title { color: rgb(31,41,55); }
.paper-meta { color: rgb(156,163,175); margin-left: 8px; }
.empty-hint { font-size: 13px; color: rgb(156,163,175); }

.button-group { display: flex; gap: 12px; justify-content: center; }

:deep(.el-card) {
  border-radius: 24px;
  border: 1px solid rgba(229, 231, 235, 0.50);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06);
}
:deep(.el-button--primary) {
  background: rgb(0, 108, 73); border-color: rgb(0, 108, 73); border-radius: 9999px;
}
:deep(.el-button--primary:hover) { background: rgb(0, 90, 60); border-color: rgb(0, 90, 60); }
:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: rgba(79, 251, 182, 0.08);
  border-color: rgb(0, 108, 73) !important;
  color: rgb(0, 108, 73);
  box-shadow: -1px 0 0 0 rgb(0,108,73);
}
</style>
