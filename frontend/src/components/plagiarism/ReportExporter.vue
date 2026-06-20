<template>
  <div class="rep-wrap">
    <button class="rep-btn" :disabled="busy" @click="exportPdf">
      {{ busy ? '生成中...' : '导出 PDF 报告' }}
    </button>

    <div ref="tplRef" class="rep-template">
      <h1 class="rep-cover-title">外文查重报告</h1>
      <p class="rep-cover-sub">{{ paperTitle || '未命名论文' }}</p>
      <p class="rep-cover-sub">生成日期: {{ dateStr }}</p>
      <p class="rep-cover-sub">
        相似度 {{ summary.rate }}% · 风险等级 {{ summary.risk_level }}
      </p>
      <hr />
      <h2>摘要</h2>
      <ul>
        <li>引擎: {{ report.engine }}</li>
        <li>档位: {{ report.paper_type || '未指定' }}</li>
        <li>总字数: {{ summary.total_chars }}</li>
        <li>命中段数: {{ highlights.length }}</li>
        <li>匹配来源数: {{ sources.length }}</li>
      </ul>
      <h2>命中明细</h2>
      <table class="rep-tbl">
        <thead>
          <tr><th>#</th><th>原文</th><th>结论</th><th>置信度</th><th>来源</th></tr>
        </thead>
        <tbody>
          <tr v-for="h in highlights" :key="h.id">
            <td>{{ h.id }}</td>
            <td>{{ h.text }}</td>
            <td>{{ h.verdict }}</td>
            <td>{{ h.confidence }}</td>
            <td>{{ sourceTitle(h.source_id) }}</td>
          </tr>
        </tbody>
      </table>
      <h2>DOI 证据清单</h2>
      <ul>
        <li v-for="s in sources" :key="s.id">
          <strong>{{ s.title }}</strong>
          <span v-if="s.author"> — {{ s.author }}</span>
          <span v-if="s.year">, {{ s.year }}</span>
          <span v-if="s.doi"> · DOI: {{ s.doi }}</span>
        </li>
      </ul>
      <p class="rep-foot">
        基于 Semantic Scholar / CORE / PubMed 摘要级比对。结果仅供参考,不构成学术判定最终依据。
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  report: { type: Object, required: true },
  paperTitle: { type: String, default: '' },
})

const busy = ref(false)
const tplRef = ref(null)

const summary = computed(() => props.report.summary || {})
const highlights = computed(() => props.report.highlights || [])
const sources = computed(() => props.report.sources || [])
const dateStr = computed(() => new Date().toLocaleDateString('zh-CN'))

function sourceTitle(id) {
  const s = sources.value.find(x => x.id === id)
  return s ? s.title : '未知来源'
}

async function exportPdf() {
  busy.value = true
  try {
    const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
      import('html2canvas'),
      import('jspdf'),
    ])
    const canvas = await html2canvas(tplRef.value, { scale: 2, backgroundColor: '#fff' })
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const imgWidth = pageWidth
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    let heightLeft = imgHeight
    let position = 0
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight
    while (heightLeft > 0) {
      position -= pageHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }
    const title = props.paperTitle || 'plagiarism_report'
    pdf.save(`查重报告_${title}_${Date.now()}.pdf`)
  } catch (e) {
    console.error('[exportPdf] 失败:', e)
    alert('导出失败: ' + (e.message || e))
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.rep-btn {
  padding: 8px 18px;
  background: #006c49;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.rep-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.rep-template {
  position: absolute;
  left: -10000px;
  top: 0;
  width: 780px;
  padding: 40px;
  background: #fff;
  font-family: 'Source Han Sans', sans-serif;
  color: #111;
}
.rep-cover-title { font-size: 28px; text-align: center; margin-top: 60px; }
.rep-cover-sub { text-align: center; color: #555; margin: 6px 0; }
.rep-tbl { width: 100%; border-collapse: collapse; font-size: 12px; }
.rep-tbl th, .rep-tbl td {
  border: 1px solid #ddd; padding: 6px; text-align: left;
  vertical-align: top;
}
.rep-foot { margin-top: 24px; color: #888; font-size: 11px; }
</style>
