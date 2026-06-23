<template>
  <div class="page-container">

    <!-- 上传区 -->
    <div v-if="store.status === 'idle'" class="upload-section">
      <div class="upload-header">
        <div class="upload-title-row">
          <h2 class="upload-title">论文查重</h2>
          <el-tag type="warning" effect="dark" size="small" class="beta-tag">🧪 新功能测试中</el-tag>
        </div>
        <p class="upload-desc">中文 AI 语义查重 + 外文国际学术库对比,双路径精准检测</p>
      </div>

      <el-tabs v-model="checkTab" @tab-change="onTabChange" class="lang-tabs">
        <el-tab-pane name="zh">
          <template #label>
            <span>中文论文查重</span>
          </template>
          <el-card class="upload-card">
            <el-form label-width="100px">
              <el-form-item label="论文类型">
                <div class="paper-type-select">
                  <el-radio-group v-model="paperType">
                    <el-radio value="">不限</el-radio>
                    <el-radio value="undergraduate">本科</el-radio>
                    <el-radio value="master">硕士</el-radio>
                    <el-radio value="doctor">博士</el-radio>
                    <el-radio value="journal">期刊</el-radio>
                  </el-radio-group>
                  <div class="paper-type-hint" v-if="currentTypeHint">ℹ {{ currentTypeHint }}</div>
                </div>
              </el-form-item>
              <el-form-item label="检测内容">
                <el-radio-group v-model="cnInputMode" size="small" style="margin-bottom:10px;">
                  <el-radio-button value="file">文件上传</el-radio-button>
                  <el-radio-button value="paste">粘贴文本</el-radio-button>
                </el-radio-group>
                <el-upload
                  v-if="cnInputMode === 'file'"
                  class="upload-dragger" drag :auto-upload="false" :limit="1"
                  accept=".docx,.txt,.pdf"
                  :on-change="handleFileChange"
                  :on-exceed="() => ElMessage.warning('只能上传一个文件')"
                >
                  <el-icon class="upload-icon" :size="48"><Upload /></el-icon>
                  <div class="upload-text">拖拽文件到此处,或 <em>点击上传</em></div>
                  <div class="upload-hint">通义千问语义查重 · 消耗 1 次额度</div>
                </el-upload>
                <el-input
                  v-else
                  v-model="pasteText" type="textarea" :rows="10" maxlength="20000" show-word-limit
                  placeholder="粘贴要检测的论文内容（适合局部/快速自查，至少 50 字）..."
                />
              </el-form-item>
            </el-form>
            <div class="upload-actions">
              <CostHint :credits="1" />
              <el-button type="primary" size="large"
                :disabled="cnInputMode === 'file' ? !selectedFile : pasteText.trim().length < 50"
                @click="handleStart">
                <el-icon><Search /></el-icon> 开始检测(中文)
              </el-button>
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane v-if="store.englishCheckEnabled" name="en">
          <template #label>
            <span>英文论文查重 <el-tag size="small" effect="dark" type="success" style="margin-left:6px;">Beta</el-tag></span>
          </template>
          <el-card class="upload-card">
            <div class="en-header">对比 Semantic Scholar · CORE · PubMed 三大国际学术库,产出 DOI 级证据</div>
            <el-form label-width="100px">
              <el-form-item label="论文类型">
                <div class="paper-type-select">
                  <el-radio-group v-model="paperType">
                    <el-radio value="undergraduate">本科（Undergraduate）</el-radio>
                    <el-radio value="master">硕士（Master）</el-radio>
                    <el-radio value="doctor">博士（PhD）</el-radio>
                    <el-radio value="journal">期刊（Journal）</el-radio>
                  </el-radio-group>
                  <div class="paper-type-hint">ℹ 连续 6 词重合即判为抄袭，标准比中文更严格</div>
                </div>
              </el-form-item>
              <el-form-item label="语言">
                <el-radio-group v-model="enLanguage">
                  <el-radio value="auto">自动检测</el-radio>
                  <el-radio value="en">English</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="上传文件">
                <el-upload
                  class="upload-dragger" drag :auto-upload="false" :limit="1"
                  accept=".docx,.txt,.pdf"
                  :on-change="handleFileChange"
                  :on-exceed="() => ElMessage.warning('只能上传一个文件')"
                >
                  <el-icon class="upload-icon" :size="48"><Upload /></el-icon>
                  <div class="upload-text">拖拽文件到此处,或 <em>点击上传</em></div>
                  <div class="upload-hint">基于摘要级比对,正文中段改写可能漏检</div>
                </el-upload>
              </el-form-item>
            </el-form>
            <div class="upload-actions">
              <CostHint :credits="enLanguage === 'en' ? 2 : 1" />
              <el-button type="primary" size="large" :disabled="!selectedFile" @click="handleStart">
                <el-icon><Search /></el-icon> 开始检测(外文)
              </el-button>
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 检测中 -->
    <div v-else-if="['uploading','pending','processing'].includes(store.status)" class="checking-section">
      <el-card class="checking-card">
        <div class="checking-content">
          <el-icon class="checking-icon" :size="64"><Loading /></el-icon>
          <h3>正在检测中...</h3>
          <p class="checking-file">{{ store.fileName }}</p>
          <div style="width: 440px; margin: 20px auto;">
            <ProgressStages :progress="store.progress" :stage="store.stage" />
          </div>
          <p class="checking-tip">
            {{ store.selectedLanguage === 'en' ? '英文论文查重预计 15~25 秒' : '中文论文查重预计 5~20 秒' }},请稍候
          </p>
        </div>
      </el-card>
    </div>

    <!-- 报告区（partial 或 done） -->
    <div v-else-if="store.report" class="report-section">

      <!-- 顶部操作栏 -->
      <div class="report-topbar">
        <div class="report-file-info">
          <span class="report-filename">📄 {{ store.fileName }}</span>
          <el-tag :type="engineTagType" size="small">{{ engineLabel }}</el-tag>
          <el-tag v-if="reportLevelLabel" type="info" size="small" effect="plain">
            参照标准：{{ reportLevelLabel }}（红线 {{ reportRedLine }}%）
          </el-tag>
          <el-tag v-if="!store.isFinal" type="warning" size="small" effect="plain">
            <el-icon class="is-loading"><Loading /></el-icon>
            AI增强检测中...
          </el-tag>
        </div>
        <div style="display:flex;gap:8px;">
          <el-button @click="handleDownload" type="success" plain>
            <el-icon><Download /></el-icon>
            下载报告
          </el-button>
          <el-button @click="handleReset">重新检测</el-button>
        </div>
      </div>

      <!-- 演示提示 -->
      <el-alert
        v-if="store.report.engine === 'opensource' || store.report.engine === 'opensource-fallback'"
        title="当前使用开源引擎，检测结果仅供参考，不代表官方查重结果"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <!-- 中文 AI 引擎诚实标注 -->
      <el-alert
        v-if="store.report.engine && String(store.report.engine).startsWith('hybrid')"
        title="中文查重为 AI 估算重复率 + 维普真实相似来源参考，非官方逐句检测报告；最终请以学校/期刊官方查重为准"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <!-- 外文引擎:降级提示 + 导出功能 -->
      <FallbackBanner v-if="isFallback" />
      <div v-if="isEnEngine" class="en-actions">
        <CopyDoiList :sources="store.report.sources" />
        <ReportExporter
          v-if="['doctor','journal'].includes(store.report.paper_type)"
          :report="store.report"
          :paper-title="store.fileName"
        />
      </div>

      <!-- 概览 -->
      <div class="overview-grid">
        <!-- 环形图 -->
        <el-card class="overview-chart-card">
          <div class="ring-chart-wrapper">
            <svg viewBox="0 0 120 120" class="ring-svg">
              <circle cx="60" cy="60" r="50" fill="none" stroke="#f0f0f0" stroke-width="12" />
              <circle
                cx="60" cy="60" r="50" fill="none"
                :stroke="rateColor"
                stroke-width="12"
                stroke-linecap="round"
                :stroke-dasharray="`${rateArc} 314`"
                stroke-dashoffset="78.5"
                style="transition: stroke-dasharray 1s ease;"
              />
            </svg>
            <div class="ring-center">
              <div class="ring-rate" :style="{ color: rateColor }">{{ store.report.summary.rate }}%</div>
              <div class="ring-label">重复率</div>
            </div>
          </div>
          <div class="risk-badge" :class="`risk-${store.report.summary.risk_level}`">
            {{ riskLabel }}
          </div>
        </el-card>

        <!-- 数据卡片 -->
        <div class="overview-stats">
          <div class="stat-card">
            <div class="stat-num">{{ store.report.summary.total_chars.toLocaleString() }}</div>
            <div class="stat-label">总字符数</div>
          </div>
          <div class="stat-card">
            <div class="stat-num">{{ store.report.summary.dup_chars.toLocaleString() }}</div>
            <div class="stat-label">重复字符数</div>
          </div>
          <div class="stat-card">
            <div class="stat-num">{{ store.report.highlights.length }}</div>
            <div class="stat-label">疑似重复段落</div>
          </div>
          <div class="stat-card">
            <div class="stat-num">{{ store.report.sources.length }}</div>
            <div class="stat-label">检出来源</div>
          </div>
        </div>
      </div>

      <!-- 期刊送审建议 -->
      <el-alert
        v-if="store.report.journal_advice"
        :title="store.report.journal_advice"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <!-- 改写建议（博士/期刊） -->
      <el-card
        v-if="store.report.rewrite_suggestions && store.report.rewrite_suggestions.length"
        class="advice-card"
        style="margin-bottom: 16px;"
      >
        <template #header>
          <div class="advice-header">
            <span>📝 改写建议（高风险片段 Top {{ store.report.rewrite_suggestions.length }}）</span>
          </div>
        </template>
        <div
          v-for="(adv, idx) in store.report.rewrite_suggestions"
          :key="adv.highlight_id || idx"
          class="advice-item"
        >
          <div class="advice-segment">
            <el-tag size="small" type="danger" effect="plain" style="margin-right:8px;">
              {{ (adv.similarity * 100).toFixed(0) }}%
            </el-tag>
            "{{ adv.segment }}"
          </div>
          <div class="advice-meta">
            <div><b>问题：</b>{{ adv.issue }}</div>
            <div><b>改写思路：</b>{{ adv.rewrite_tip }}</div>
            <div v-if="adv.citation_template"><b>建议引用：</b>{{ adv.citation_template }}</div>
          </div>
        </div>
      </el-card>

      <!-- 详情 Tabs -->
      <el-card class="detail-card">
        <el-tabs v-model="activeTab">

          <!-- 原文高亮 -->
          <el-tab-pane label="原文高亮" name="highlight">
            <div class="highlight-layout">
              <div class="highlight-text" v-html="highlightedText"></div>
              <div class="source-panel">
                <div class="source-panel-title">来源文献({{ store.report.sources.length }} 篇)</div>
                <template v-if="isEnEngine">
                  <SourceCardEn
                    v-for="src in store.report.sources"
                    :key="src.id"
                    :source="src"
                    :similarity="getMaxSimilarity(src.id)"
                    :confidence="getMaxConfidence(src.id)"
                    :ngram-hit="hasNgramHit(src.id)"
                  />
                </template>
                <template v-else>
                  <div
                    v-for="src in store.report.sources"
                    :key="src.id"
                    class="source-item"
                    :class="{ active: activeSourceId === src.id }"
                    @click="handleSourceClick(src.id)"
                  >
                    <div class="source-title">{{ src.title }}</div>
                    <div class="source-meta">
                      <span>{{ src.author }}</span>
                      <span v-if="src.year">· {{ src.year }}</span>
                      <el-tag size="small" :type="getSimilarityTag(getMaxSimilarity(src.id))">
                        {{ (getMaxSimilarity(src.id) * 100).toFixed(0) }}%
                      </el-tag>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </el-tab-pane>

          <!-- 片段列表 -->
          <el-tab-pane label="片段列表" name="segments">
            <el-table :data="store.report.highlights" stripe>
              <el-table-column label="片段内容" min-width="300">
                <template #default="{ row }">
                  <span class="segment-text">{{ row.text }}</span>
                  <el-tag v-if="row.ai_judged" size="small" type="primary" style="margin-left: 6px;">AI</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="相似度" width="100">
                <template #default="{ row }">
                  <el-tag :type="getSimilarityTag(row.similarity)">
                    {{ (row.similarity * 100).toFixed(0) }}%
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="判定" width="120">
                <template #default="{ row }">{{ row.verdict || '疑似重复' }}</template>
              </el-table-column>
              <el-table-column label="来源" min-width="200">
                <template #default="{ row }">
                  {{ getSourceTitle(row.source_id) }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 来源详情 -->
          <el-tab-pane label="来源详情" name="sources">
            <div v-for="src in store.report.sources" :key="src.id" class="source-detail-item">
              <div class="source-detail-header">
                <span class="source-detail-title">{{ src.title }}</span>
                <el-tag :type="getSimilarityTag(getMaxSimilarity(src.id))">
                  最高相似度 {{ (getMaxSimilarity(src.id) * 100).toFixed(0) }}%
                </el-tag>
              </div>
              <div class="source-detail-meta">
                <span v-if="src.author">作者：{{ src.author }}</span>
                <span v-if="src.year">年份：{{ src.year }}</span>
                <a v-if="src.url" :href="src.url" target="_blank">查看原文</a>
              </div>
              <div class="source-segments">
                <div
                  v-for="h in getHighlightsBySource(src.id)"
                  :key="h.id"
                  class="source-segment-text"
                >
                  "{{ h.text }}"
                </div>
              </div>
            </div>
          </el-tab-pane>

        </el-tabs>
      </el-card>
    </div>

    <!-- 失败状态 -->
    <div v-else-if="store.status === 'failed'" class="failed-section">
      <el-result icon="error" :title="store.errorMsg || '检测失败'">
        <template #extra>
          <el-button type="primary" @click="handleReset">重新检测</el-button>
        </template>
      </el-result>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { Upload, Search, Loading, Download } from '@element-plus/icons-vue'
import { usePlagiarismStore } from '@/store/modules/plagiarism'
import CostHint from '@/components/common/CostHint.vue'
import FallbackBanner from '@/components/plagiarism/FallbackBanner.vue'
import ProgressStages from '@/components/plagiarism/ProgressStages.vue'
import CopyDoiList from '@/components/plagiarism/CopyDoiList.vue'
import ReportExporter from '@/components/plagiarism/ReportExporter.vue'
import SourceCardEn from '@/components/plagiarism/SourceCardEn.vue'

const store = usePlagiarismStore()
const router = useRouter()

const selectedFile = ref(null)
const cnInputMode = ref('file')   // 中文查重输入方式：file 文件 / paste 粘贴文本
const pasteText = ref('')
const paperType = ref('')
const activeTab = ref('highlight')
const activeSourceId = ref(null)

// 双 Tab + 语言
const checkTab = ref('zh')
const enLanguage = ref('auto')

onMounted(() => {
  store.loadConfig()
})

function onTabChange(tab) {
  store.setActiveTab(tab)
  selectedFile.value = null
  paperType.value = tab === 'en' ? 'master' : ''
}

const isEnEngine = computed(() => {
  const e = store.report?.engine
  return e === 'english_academic' || e === 'english_academic_fallback'
})
const isFallback = computed(() => store.report?.engine === 'english_academic_fallback')

// 论文类型 → 评判尺度提示(与后端 levels.py 保持一致)
const PAPER_TYPE_HINTS = {
  '': '不限类型，重复率 ≥40% 标记高风险，适合初步自查',
  'undergraduate': '本科毕业论文：重复率红线 30%，容忍专业术语及常见引用句式',
  'master': '硕士学位论文：重复率红线 20%，可识别段落改写式抄袭',
  'doctor': '博士学位论文：重复率红线 10%，严格检测观点借用与方法抄袭',
  'journal': '期刊投稿：重复率红线 15%，按审稿标准判定，含改写建议',
}
const currentTypeHint = computed(() => PAPER_TYPE_HINTS[paperType.value] ?? '')

// 文件选择
function handleFileChange(file) {
  selectedFile.value = file.raw
}

// 开始检测
async function handleStart() {
  const lang = checkTab.value === 'en' ? enLanguage.value : 'zh'
  // 中文 Tab 的「粘贴文本」模式
  const usePaste = checkTab.value === 'zh' && cnInputMode.value === 'paste'

  if (usePaste) {
    if (pasteText.value.trim().length < 50) {
      ElMessage.warning('粘贴内容过短（至少 50 字）')
      return
    }
  } else {
    if (!selectedFile.value) return
    if (selectedFile.value.size === 0) {
      ElMessage.error('文件内容为空，请重新选择')
      return
    }
    const MAX_SIZE = 20 * 1024 * 1024
    if (selectedFile.value.size > MAX_SIZE) {
      ElMessage.error('文件大小超过 20MB，请压缩后重试')
      return
    }
  }

  try {
    await store.startCheck(
      usePaste ? null : selectedFile.value,
      paperType.value, lang,
      usePaste ? pasteText.value.trim() : '',
    )
  } catch (e) {
    if (e?.response?.status === 402) {
      ElMessageBox.confirm(
        '本次操作失败，您的可用次数已不足，可前往购买',
        '次数不足',
        {
          confirmButtonText: '去购买',
          cancelButtonText: '暂不购买',
          confirmButtonClass: 'el-button--primary',
          customStyle: { '--el-color-primary': 'rgb(0, 108, 73)' },
          showClose: false,
        }
      ).then(() => {
        router.push('/pricing')
      }).catch(() => {})
    } else {
      ElMessage.error('上传失败：' + (e?.response?.data?.detail || e.message))
    }
  }
}

// 下载 PDF 报告
async function handleDownload() {
  if (!store.report) return
  const { default: jsPDF } = await import('jspdf')
  const { default: html2canvas } = await import('html2canvas')

  const r = store.report
  const riskMap = { low: '低风险', medium: '中风险', high: '高风险' }
  const snap = r.threshold_snapshot || {}
  const standardLine = snap.paper_type
    ? `参照标准：${snap.label}（红线 ${snap.rate_high}% / 中风险 ${snap.rate_medium}%）`
    : '参照标准：通用'
  const adviceBlock = (r.rewrite_suggestions && r.rewrite_suggestions.length)
    ? `
    <h2 style="font-size:16px;border-left:4px solid #409EFF;padding-left:10px;margin-bottom:12px;">改写建议（Top ${r.rewrite_suggestions.length}）</h2>
    ${r.rewrite_suggestions.map((a, i) => `
      <div style="margin-bottom:12px;padding:10px;background:#f4f8ff;border-radius:6px;border-left:3px solid #409EFF;">
        <div style="font-size:12px;color:#666;margin-bottom:4px;">建议 ${i+1} · 相似度 ${(a.similarity*100).toFixed(0)}%</div>
        <div style="font-size:13px;margin-bottom:4px;">原片段："${(a.segment||'').slice(0,160)}${(a.segment||'').length>160?'...':''}"</div>
        <div style="font-size:13px;"><b>问题：</b>${a.issue||'-'}</div>
        <div style="font-size:13px;"><b>改写思路：</b>${a.rewrite_tip||'-'}</div>
        ${a.citation_template?`<div style="font-size:13px;"><b>建议引用：</b>${a.citation_template}</div>`:''}
      </div>
    `).join('')}`
    : ''
  const journalBlock = r.journal_advice
    ? `
    <h2 style="font-size:16px;border-left:4px solid #67C23A;padding-left:10px;margin-bottom:12px;">期刊送审建议</h2>
    <div style="margin-bottom:16px;padding:10px 14px;background:#f0f9eb;border-radius:6px;font-size:13px;">${r.journal_advice}</div>`
    : ''

  // 创建一个临时 div 渲染报告内容
  const el = document.createElement('div')
  el.style.cssText = 'position:fixed;left:-9999px;top:0;width:794px;padding:40px;background:#fff;font-family:SimSun,serif;font-size:14px;color:#333;line-height:1.8;'
  el.innerHTML = `
    <h1 style="text-align:center;font-size:22px;margin-bottom:4px;">论文查重报告</h1>
    <p style="text-align:center;color:#999;font-size:12px;margin-bottom:8px;">
      检测时间：${r.created_at ? r.created_at.replace('T',' ').slice(0,19) : new Date().toLocaleString()}
      &nbsp;&nbsp;引擎：${r.engine}
    </p>
    <p style="text-align:center;color:#666;font-size:12px;margin-bottom:24px;">${standardLine}</p>
    <hr style="border:none;border-top:2px solid #eee;margin-bottom:20px;"/>

    <h2 style="font-size:16px;border-left:4px solid #006C49;padding-left:10px;margin-bottom:12px;">检测概览</h2>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
      <tr>
        <td style="padding:8px 12px;background:#f5f7fa;width:25%;">文件名</td>
        <td style="padding:8px 12px;">${store.fileName}</td>
        <td style="padding:8px 12px;background:#f5f7fa;width:25%;">重复率</td>
        <td style="padding:8px 12px;color:${r.summary.rate>=40?'#F56C6C':r.summary.rate>=20?'#E6A23C':'#67C23A'};font-weight:bold;">${r.summary.rate}%</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;background:#f5f7fa;">风险等级</td>
        <td style="padding:8px 12px;">${riskMap[r.summary.risk_level] || r.summary.risk_level}</td>
        <td style="padding:8px 12px;background:#f5f7fa;">总字符数</td>
        <td style="padding:8px 12px;">${r.summary.total_chars.toLocaleString()}</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;background:#f5f7fa;">重复字符数</td>
        <td style="padding:8px 12px;">${r.summary.dup_chars.toLocaleString()}</td>
        <td style="padding:8px 12px;background:#f5f7fa;">疑似重复段落</td>
        <td style="padding:8px 12px;">${r.highlights.length} 处</td>
      </tr>
    </table>

    <h2 style="font-size:16px;border-left:4px solid #006C49;padding-left:10px;margin-bottom:12px;">来源文献（${r.sources.length} 篇）</h2>
    <ol style="margin:0 0 20px 20px;padding:0;">
      ${r.sources.map(s => `<li style="margin-bottom:6px;">${s.title}</li>`).join('')}
    </ol>

    ${journalBlock}
    ${adviceBlock}

    <h2 style="font-size:16px;border-left:4px solid #E6A23C;padding-left:10px;margin-bottom:12px;">疑似重复片段详情</h2>
    ${r.highlights.map((h, i) => `
      <div style="margin-bottom:14px;padding:12px;background:#fef9f0;border-radius:6px;border-left:3px solid ${h.similarity>=0.8?'#F56C6C':h.similarity>=0.6?'#E6A23C':'#67C23A'};">
        <div style="display:flex;gap:16px;margin-bottom:6px;font-size:12px;color:#666;">
          <span>片段 ${i+1}</span>
          <span>相似度：<b style="color:${h.similarity>=0.8?'#F56C6C':'#E6A23C'}">${(h.similarity*100).toFixed(0)}%</b></span>
          <span>判定：${h.verdict}</span>
          <span>来源：${r.sources.find(s=>s.id===h.source_id)?.title || '未知'}</span>
        </div>
        <div style="font-size:13px;color:#333;">${h.text.slice(0,200)}${h.text.length>200?'...':''}</div>
      </div>
    `).join('')}
  `
  document.body.appendChild(el)

  try {
    ElMessage.info('正在生成 PDF，请稍候...')
    const canvas = await html2canvas(el, { scale: 2, useCORS: true, backgroundColor: '#fff' })
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageW = 210
    const pageH = 297
    const imgW = pageW
    const imgH = (canvas.height * imgW) / canvas.width
    let y = 0
    while (y < imgH) {
      if (y > 0) pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, -y, imgW, imgH)
      y += pageH
    }
    pdf.save(`查重报告_${store.fileName.replace(/\.[^.]+$/, '')}.pdf`)
    ElMessage.success('PDF 已下载')
  } finally {
    document.body.removeChild(el)
  }
}

// 重置
function handleReset() {
  store.reset()
  selectedFile.value = null
  paperType.value = ''
  activeTab.value = 'highlight'
  activeSourceId.value = null
}

// 点击来源
function handleSourceClick(sourceId) {
  activeSourceId.value = sourceId
  // 滚动到第一个对应高亮片段
  const el = document.querySelector(`.hl-src-${sourceId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('hl-flash')
    setTimeout(() => el.classList.remove('hl-flash'), 1200)
  }
}

// 重复率颜色
const rateColor = computed(() => {
  const r = store.report?.summary?.rate ?? 0
  if (r >= 40) return '#F56C6C'
  if (r >= 20) return '#E6A23C'
  return '#67C23A'
})

// 环形图弧长（周长 314）
const rateArc = computed(() => {
  const r = store.report?.summary?.rate ?? 0
  return ((r / 100) * 314).toFixed(1)
})

// 风险等级文字
const riskLabel = computed(() => {
  const map = { low: '低风险', medium: '中风险', high: '高风险' }
  return map[store.report?.summary?.risk_level] ?? '未知'
})

// 引擎标签文字
const engineLabel = computed(() => {
  const map = {
    'opensource': '开源引擎 V1',
    'opensource-fallback': '开源引擎（降级）',
    'hybrid-bailian': '混合引擎 V2',
  }
  return map[store.report?.engine] ?? store.report?.engine ?? ''
})

// 引擎标签类型
const engineTagType = computed(() => {
  if (store.report?.engine === 'hybrid-bailian') return 'primary'
  if (store.report?.engine?.includes('fallback')) return 'warning'
  return 'info'
})

// 当前报告的参照标准(来自后端 threshold_snapshot)
const reportLevelLabel = computed(() => {
  const snap = store.report?.threshold_snapshot
  if (!snap) return ''
  // 不限/空档不展示标准徽章,避免视觉噪音
  if (!snap.paper_type) return ''
  return snap.label || ''
})
const reportRedLine = computed(() => {
  const snap = store.report?.threshold_snapshot
  return snap?.rate_high ?? ''
})

// 原文高亮 HTML
const highlightedText = computed(() => {
  if (!store.report) return ''
  // 简单实现：将 highlights 按 start_pos 排序，逐段插入 span
  const text = store.report.raw_text || ''
  if (!text) {
    // 无原文时，直接列出片段
    return store.report.highlights.map(h => {
      const color = getHighlightColor(h.similarity)
      return `<span class="hl hl-src-${h.source_id}" style="background:${color}20;border-bottom:2px solid ${color};border-radius:2px;padding:1px 2px;" title="${(h.similarity*100).toFixed(0)}% 相似">${h.text}</span>`
    }).join('<br/><br/>')
  }
  // 有原文时按位置插入
  const sorted = [...store.report.highlights].sort((a, b) => a.start_pos - b.start_pos)
  let result = ''
  let cursor = 0
  for (const h of sorted) {
    if (h.start_pos > cursor) result += escapeHtml(text.slice(cursor, h.start_pos))
    const color = getHighlightColor(h.similarity)
    const aiTag = h.ai_judged ? '<sup style="color:#006C49;font-size:10px;">AI</sup>' : ''
    result += `<span class="hl hl-src-${h.source_id}" style="background:${color}20;border-bottom:2px solid ${color};border-radius:2px;padding:1px 2px;">${escapeHtml(text.slice(h.start_pos, h.end_pos))}${aiTag}</span>`
    cursor = h.end_pos
  }
  result += escapeHtml(text.slice(cursor))
  return result
})

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

function getHighlightColor(similarity) {
  if (similarity >= 0.8) return '#F56C6C'
  if (similarity >= 0.6) return '#E6A23C'
  return '#67C23A'
}

function getSimilarityTag(similarity) {
  if (similarity >= 0.8) return 'danger'
  if (similarity >= 0.6) return 'warning'
  return 'success'
}

function getMaxSimilarity(sourceId) {
  if (!store.report) return 0
  const hs = store.report.highlights.filter(h => h.source_id === sourceId)
  return hs.length ? Math.max(...hs.map(h => h.similarity)) : 0
}

function getMaxConfidence(sourceId) {
  if (!store.report) return 0
  const hs = store.report.highlights.filter(h => h.source_id === sourceId)
  return hs.length ? Math.max(...hs.map(h => h.confidence || 0)) : 0
}

function hasNgramHit(sourceId) {
  if (!store.report) return false
  return store.report.highlights.some(h => h.source_id === sourceId && h.ngram_hit)
}

function getHighlightsBySource(sourceId) {
  return store.report?.highlights?.filter(h => h.source_id === sourceId) ?? []
}

function getSourceTitle(sourceId) {
  return store.report?.sources?.find(s => s.id === sourceId)?.title ?? sourceId
}
</script>

<style scoped>
/* 上传区 */
.upload-section { max-width: 760px; margin: 0 auto; }
.upload-header { text-align: center; margin-bottom: 24px; }
.upload-title-row { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 8px; }
.upload-title { font-size: 30px; font-weight: 400; margin: 0; color: rgb(18, 18, 18); }
.beta-tag { font-size: 12px; vertical-align: middle; }
.upload-desc { color: rgb(107, 114, 128); font-size: 16px; margin: 0; line-height: 26px; }
.upload-card { border-radius: 24px; }
.upload-dragger { width: 100%; }
.upload-icon { color: rgb(107, 114, 128); }
.upload-text { font-size: 15px; color: rgb(107, 114, 128); margin-top: 8px; }
.upload-text em { color: rgb(0, 108, 73); font-style: normal; }
.upload-hint { font-size: 12px; color: rgb(107, 114, 128); margin-top: 4px; }
.upload-actions { display: flex; justify-content: center; margin-top: 20px; }
.paper-type-select {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.paper-type-hint {
  font-size: 12px;
  color: rgb(107, 114, 128);
  line-height: 1.6;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 4px 8px;
}

/* 改写建议卡片 */
.advice-card { border-radius: 24px; }
.advice-header { font-size: 15px; font-weight: 600; color: rgb(18, 18, 18); }
.advice-item {
  padding: 12px 14px; background: rgb(249, 249, 249);
  border-radius: 12px; margin-bottom: 10px;
  border-left: 3px solid rgb(0, 108, 73);
}
.advice-item:last-child { margin-bottom: 0; }
.advice-segment {
  font-size: 13px; color: rgb(18, 18, 18);
  margin-bottom: 8px; line-height: 1.6;
}
.advice-meta {
  font-size: 13px; color: rgb(55, 65, 81);
  display: flex; flex-direction: column; gap: 4px;
}

/* 检测中 */
.checking-section { max-width: 600px; margin: 60px auto; }
.checking-card { border-radius: 24px; }
.checking-content { text-align: center; padding: 40px 20px; }
.checking-icon { color: rgb(0, 108, 73); animation: spin 1.5s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.checking-file { color: rgb(107, 114, 128); font-size: 14px; margin: 8px 0; }
.checking-tip { color: rgb(107, 114, 128); font-size: 13px; }

/* 报告顶栏 */
.report-topbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; flex-wrap: wrap; gap: 10px;
}
.report-file-info { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.report-filename { font-size: 15px; font-weight: 500; }

/* 概览 */
.overview-grid {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 640px) { .overview-grid { grid-template-columns: 1fr; } }

.overview-chart-card { border-radius: 24px; display: flex; flex-direction: column; align-items: center; padding: 20px; }
.ring-chart-wrapper { position: relative; width: 140px; height: 140px; }
.ring-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.ring-center {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  text-align: center;
}
.ring-rate { font-family: 'Newsreader', serif; font-style: italic; font-size: 28px; font-weight: 700; line-height: 1; }
.ring-label { font-size: 12px; color: rgb(107, 114, 128); margin-top: 4px; }
.risk-badge {
  margin-top: 12px; padding: 4px 16px; border-radius: 20px;
  font-size: 13px; font-weight: 600;
}
.risk-low { background: #f0f9eb; color: #67C23A; }
.risk-medium { background: #fdf6ec; color: #E6A23C; }
.risk-high { background: #fef0f0; color: #F56C6C; }

.overview-stats {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; align-content: start;
}
.stat-card {
  background: rgb(249, 249, 249); border-radius: 16px; padding: 16px;
  text-align: center;
}
.stat-num { font-family: 'Newsreader', serif; font-style: italic; font-size: 24px; font-weight: 700; color: rgb(18, 18, 18); }
.stat-label { font-size: 12px; color: rgb(107, 114, 128); margin-top: 4px; }

/* 详情 */
.detail-card { border-radius: 24px; }
.highlight-layout { display: flex; gap: 16px; min-height: 300px; }
.highlight-text {
  flex: 1; line-height: 2; font-size: 14px; color: rgb(18, 18, 18);
  white-space: pre-wrap; word-break: break-all;
}
.source-panel { width: 240px; flex-shrink: 0; border-left: 1px solid rgba(229, 231, 235, 0.50); padding-left: 16px; }
.source-panel-title { font-size: 13px; font-weight: 600; color: rgb(107, 114, 128); margin-bottom: 10px; }
.source-item {
  padding: 8px 10px; border-radius: 8px; cursor: pointer;
  margin-bottom: 8px; transition: background 0.2s;
}
.source-item:hover, .source-item.active { background: rgba(79, 251, 182, 0.08); }
.source-title { font-size: 13px; color: rgb(18, 18, 18); font-weight: 500; }
.source-meta { font-size: 12px; color: rgb(107, 114, 128); margin-top: 4px; display: flex; gap: 6px; align-items: center; }

.segment-text { font-size: 13px; color: rgb(18, 18, 18); }

.source-detail-item { padding: 16px 0; border-bottom: 1px solid rgba(229, 231, 235, 0.50); }
.source-detail-item:last-child { border-bottom: none; }
.source-detail-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.source-detail-title { font-size: 15px; font-weight: 600; }
.source-detail-meta { font-size: 13px; color: rgb(107, 114, 128); display: flex; gap: 16px; margin-bottom: 8px; }
.source-detail-meta a { color: rgb(0, 108, 73); }
.source-segments { display: flex; flex-direction: column; gap: 6px; }
.source-segment-text {
  font-size: 13px; color: rgb(107, 114, 128); background: rgb(249, 249, 249);
  border-radius: 12px; padding: 6px 10px; border-left: 3px solid #E6A23C;
}

/* 失败 */
.failed-section { max-width: 500px; margin: 60px auto; }

/* 高亮闪烁动画 */
:global(.hl-flash) { animation: flash 0.6s ease 2; }
@keyframes flash { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

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
