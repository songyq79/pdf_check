<template>
  <div class="src-card src-card--en">
    <div class="src-head">
      <span class="src-badge" :class="badgeClass">{{ badgeLabel }}</span>
      <span v-if="confidence != null" class="src-conf" :class="confClass">
        置信度 {{ confidence }}
      </span>
      <span v-if="ngramHit" class="src-ngram">连续词命中</span>
    </div>
    <div class="src-title">{{ source.title || 'Unknown source' }}</div>
    <div class="src-meta">
      <span v-if="source.author">{{ source.author }}</span>
      <span v-if="source.year">· {{ source.year }}</span>
      <span v-if="similarity != null" class="src-sim">
        sim {{ (similarity * 100).toFixed(1) }}%
      </span>
    </div>
    <a v-if="source.doi" class="src-doi" :href="`https://doi.org/${source.doi}`"
       target="_blank" rel="noopener">
      DOI: {{ source.doi }}
    </a>
    <div v-if="source.abstract" class="src-abstract-wrap">
      <button class="src-toggle" @click="expanded = !expanded">
        {{ expanded ? '收起对比段落' : '查看对比段落' }}
      </button>
      <p v-if="expanded" class="src-abstract">{{ source.abstract }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  source: { type: Object, required: true },
  similarity: { type: Number, default: null },
  confidence: { type: Number, default: null },
  ngramHit: { type: Boolean, default: false },
})

const expanded = ref(false)

const badgeClass = computed(() => {
  switch (props.source.source_name) {
    case 'semantic_scholar': return 'badge-ss'
    case 'core': return 'badge-core'
    case 'pubmed': return 'badge-pubmed'
    default: return 'badge-default'
  }
})

const badgeLabel = computed(() => {
  switch (props.source.source_name) {
    case 'semantic_scholar': return 'Semantic Scholar'
    case 'core': return 'CORE'
    case 'pubmed': return 'PubMed'
    default: return 'External'
  }
})

const confClass = computed(() => {
  const c = props.confidence ?? 0
  if (c >= 80) return 'conf-high'
  if (c >= 50) return 'conf-mid'
  return 'conf-low'
})
</script>

<style scoped>
.src-card {
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  margin-bottom: 10px;
}
.src-head {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.src-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  color: #fff;
}
.badge-ss { background: #2563eb; }
.badge-core { background: #059669; }
.badge-pubmed { background: #7c3aed; }
.badge-default { background: #6b7280; }

.src-conf {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: auto;
}
.conf-high { background: #d1fae5; color: #047857; }
.conf-mid { background: #fef3c7; color: #92400e; }
.conf-low { background: #fee2e2; color: #b91c1c; }

.src-ngram {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #fde68a;
  color: #78350f;
  font-weight: 500;
}

.src-title {
  font-weight: 500;
  color: #111827;
  margin-bottom: 4px;
}

.src-meta {
  font-size: 12px;
  color: #6b7280;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.src-sim {
  margin-left: auto;
  color: #006c49;
  font-weight: 500;
}

.src-doi {
  font-size: 12px;
  color: #2563eb;
  text-decoration: none;
  display: inline-block;
  margin-top: 4px;
}
.src-doi:hover { text-decoration: underline; }

.src-toggle {
  margin-top: 8px;
  background: transparent;
  border: none;
  color: #006c49;
  cursor: pointer;
  font-size: 12px;
  padding: 0;
}
.src-abstract {
  font-size: 12px;
  color: #4b5563;
  line-height: 1.6;
  margin-top: 6px;
  padding: 8px;
  background: #f9fafb;
  border-radius: 6px;
}
</style>
