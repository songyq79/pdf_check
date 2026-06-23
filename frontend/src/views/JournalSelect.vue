<template>
  <div class="page-container">
    <div class="page-title">投稿选刊</div>
    <div class="page-description">
      粘贴论文标题、关键词、摘要，AI 按<strong>主题语义</strong>为你匹配最契合的期刊（基于本地期刊库，免费）。
    </div>

    <el-card class="mb-20">
      <el-form label-position="top">
        <el-form-item label="论文标题">
          <el-input v-model="form.title" placeholder="论文标题" />
        </el-form-item>
        <el-form-item label="摘要">
          <el-input v-model="form.abstract" type="textarea" :rows="5" maxlength="2000" show-word-limit
            placeholder="粘贴论文摘要（越完整匹配越准）" />
        </el-form-item>
        <div class="form-row">
          <el-form-item label="关键词" class="form-col">
            <el-input v-model="form.keywords" placeholder="多个用逗号分隔" />
          </el-form-item>
          <el-form-item label="论文类别" class="form-col">
            <el-select v-model="form.paper_type" placeholder="不限" style="width:100%" clearable>
              <el-option label="人文社科类" value="humanities" />
              <el-option label="理工农医类" value="science_engineering" />
              <el-option label="艺术类" value="arts" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <div style="text-align:right;">
        <el-button type="primary" size="large" :loading="loading" @click="handleSelect">开始选刊</el-button>
      </div>
    </el-card>

    <div v-if="journals.length">
      <div class="result-head mb-20">
        匹配到 <b>{{ journals.length }}</b> 本期刊
        <span class="match-note" v-if="matchedBy === 'cqvip'">（基于维普「相似文献去向」：该主题论文常发表于这些期刊）</span>
        <span class="match-note" v-else-if="matchedBy === 'semantic'">（按主题语义排序）</span>
        <span class="match-note" v-else>（语义模型不可用，已按类别粗排）</span>
      </div>
      <el-card v-for="(j, i) in journals" :key="j.id" class="journal-card mb-20">
        <div class="jc-head">
          <span class="jc-rank">{{ i + 1 }}</span>
          <span class="jc-name">{{ j.name_zh || j.name_en || '未命名期刊' }}</span>
          <span v-if="j.evidence_count" class="jc-evidence">{{ j.evidence_count }} 篇相似论文发表于此</span>
          <span v-else class="jc-match" :style="{ color: matchColor(j.match_score) }">匹配度 {{ j.match_score }}/10</span>
        </div>
        <div class="jc-meta">
          <template v-if="j.category">
            <el-tag v-for="tag in String(j.category).split('、')" :key="tag" size="small" type="info">{{ tag }}</el-tag>
          </template>
          <el-tag v-if="j.jcr_rank" size="small">{{ j.jcr_rank }}</el-tag>
          <span v-if="j.impact_factor">IF {{ j.impact_factor }}</span>
          <span v-if="j.review_days_avg">审稿约 {{ j.review_days_avg }} 天</span>
          <span v-if="j.acceptance_rate">录取率 {{ (j.acceptance_rate * 100).toFixed(0) }}%</span>
          <el-tag v-if="j.is_open_access" size="small" type="success">OA</el-tag>
        </div>
        <div v-if="j.samples && j.samples.length" class="jc-sample">例：{{ j.samples[0] }}</div>
        <div class="jc-actions">
          <a v-if="j.submission_url" :href="j.submission_url" target="_blank" rel="noopener" class="jc-link">官方投稿入口 →</a>
          <el-button text size="small" :loading="detailLoading === j.name_zh" @click="toggleDetail(j)">
            {{ details[j.name_zh] ? '收起详情' : '查看详情' }}
          </el-button>
        </div>
        <!-- 维普期刊详情 -->
        <div v-if="details[j.name_zh]" class="jc-detail">
          <div class="jd-grid">
            <div v-if="details[j.name_zh].impact_factor"><span>影响因子</span>{{ Number(details[j.name_zh].impact_factor).toFixed(3) }}</div>
            <div v-if="details[j.name_zh].cas_part"><span>中科院分区</span>{{ details[j.name_zh].cas_part }}</div>
            <div v-if="details[j.name_zh].jcr_part"><span>JCR分区</span>{{ details[j.name_zh].jcr_part }}</div>
            <div v-if="details[j.name_zh].review_speed"><span>审稿周期</span>{{ details[j.name_zh].review_speed }}</div>
            <div v-if="details[j.name_zh].issn"><span>ISSN</span>{{ details[j.name_zh].issn }}</div>
            <div v-if="details[j.name_zh].cnno"><span>CN号</span>{{ details[j.name_zh].cnno }}</div>
            <div v-if="details[j.name_zh].publisher"><span>主办单位</span>{{ details[j.name_zh].publisher }}</div>
            <div><span>开放获取</span>{{ details[j.name_zh].is_oa ? '是(OA)' : '否' }}</div>
          </div>
          <div v-if="(details[j.name_zh].core_tags || []).length" class="jd-tags">
            <el-tag v-for="t in details[j.name_zh].core_tags" :key="t" size="small" type="success" effect="plain">{{ t }}</el-tag>
          </div>
          <div v-if="details[j.name_zh].intro" class="jd-intro">{{ details[j.name_zh].intro }}</div>
        </div>
      </el-card>
    </div>

    <el-empty v-else-if="searched && !loading" description="未匹配到期刊，换个关键词试试，或期刊库尚在扩充中" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import evaluationAPI from '@/api/evaluation'

const form = ref({ title: '', abstract: '', keywords: '', paper_type: '' })
const loading = ref(false)
const searched = ref(false)
const journals = ref([])
const matchedBy = ref('semantic')
const details = ref({})          // 刊名 -> 维普详情
const detailLoading = ref('')

async function toggleDetail(j) {
  const name = j.name_zh
  if (details.value[name]) { delete details.value[name]; details.value = { ...details.value }; return }
  detailLoading.value = name
  try {
    const d = await evaluationAPI.journalDetailByName(name)
    details.value = { ...details.value, [name]: d }
  } catch (e) {
    ElMessage.info('未查询到该期刊详情')
  } finally {
    detailLoading.value = ''
  }
}

function matchColor(s) {
  if (s >= 8) return '#008000'
  if (s >= 6) return '#0064c8'
  if (s >= 4) return '#d97706'
  return '#9ca3af'
}

async function handleSelect() {
  if (!form.value.title.trim() && !form.value.abstract.trim() && !form.value.keywords.trim()) {
    ElMessage.warning('请至少填写标题、摘要或关键词之一')
    return
  }
  loading.value = true
  try {
    const res = await evaluationAPI.journalSelect(form.value)
    journals.value = res.journals || []
    matchedBy.value = res.matched_by || 'semantic'
    searched.value = true
  } catch (e) { /* 拦截器处理 */ } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-row { display: flex; gap: 16px; }
.form-col { flex: 1; }
.result-head { font-size: 15px; color: rgb(31,41,55); }
.match-note { font-size: 13px; color: rgb(107,114,128); margin-left: 6px; }

.journal-card .jc-head { display: flex; align-items: center; gap: 12px; }
.jc-rank { width: 24px; height: 24px; border-radius: 50%; background: #006C49; color: #fff; font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.jc-name { font-size: 16px; font-weight: 700; color: rgb(17,24,39); flex: 1; }
.jc-match { font-size: 14px; font-weight: 600; }
.jc-evidence { font-size: 13px; font-weight: 600; color: #006C49; background: #E8F5EE; padding: 2px 10px; border-radius: 100px; }
.jc-sample { font-size: 12px; color: rgb(107,114,128); margin-top: 8px; }
.jc-meta { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 10px; font-size: 13px; color: rgb(107,114,128); }
.jc-actions { margin-top: 10px; display: flex; align-items: center; gap: 16px; }
.jc-link { color: #006C49; font-size: 13px; font-weight: 600; text-decoration: none; }
.jc-link:hover { text-decoration: underline; }

.jc-detail { margin-top: 12px; padding: 12px 14px; background: #f9fafb; border-radius: 10px; }
.jd-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px 18px; font-size: 13px; color: rgb(31,41,55); }
.jd-grid > div span { color: rgb(107,114,128); margin-right: 8px; }
.jd-tags { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
.jd-intro { margin-top: 10px; font-size: 12px; color: rgb(107,114,128); line-height: 1.6; }

:deep(.el-card) { border-radius: 16px; border: 1px solid rgba(229,231,235,0.6); box-shadow: 0 2px 16px rgba(0,0,0,0.05); }
:deep(.el-button--primary) { background: rgb(0,108,73); border-color: rgb(0,108,73); border-radius: 9999px; }
:deep(.el-button--primary:hover) { background: rgb(0,90,60); border-color: rgb(0,90,60); }
</style>
