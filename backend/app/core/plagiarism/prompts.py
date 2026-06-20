"""
V2 百炼提示词 + 分级严格度注入
"""

# ─────────────────────────────────────────────────────────────
# 分级严格度提示(由 levels.py 的 strictness 档位选用)
# ─────────────────────────────────────────────────────────────

_STRICTNESS_HINT = {
    "lenient": (
        "【评判尺度:本科论文】\n"
        "- 容忍专业术语、教科书定义、常见学术套语(如\"综上所述\"\"研究表明\")的重复\n"
        "- 重点关注直接抄袭与大段复制\n"
        "- 改写式相似只要核心论点相近即可判通用表述"
    ),
    "standard": (
        "【评判尺度:硕士论文】\n"
        "- 能识别改写式抄袭(句式改写但观点、结构保留)\n"
        "- 专业术语重复可容忍,但整段论证逻辑相近需警惕\n"
        "- 重点关注文献综述、方法介绍等易套用章节"
    ),
    "strict": (
        "【评判尺度:博士论文】\n"
        "- 严格识别观点、论证路径、研究方法层面的剽窃,即使文字完全改写\n"
        "- 博士论文要求原创性贡献,任何核心思想借用未标注即视为学术不端\n"
        "- 发现高相似片段请直接判定为\"疑似改写抄袭\"或\"直接抄袭\""
    ),
    "journal": (
        "【评判尺度:期刊投稿】\n"
        "- 按期刊投稿标准评判,对方法描述、数据展示、结果复用一律警惕\n"
        "- 自引(作者以前发表的内容)也需识别并标注\n"
        "- 发现问题按期刊 reject 标准描述,给出具体证据"
    ),
}


def get_strictness_hint(strictness: str) -> str:
    """未匹配时回落到 standard。"""
    return _STRICTNESS_HINT.get(strictness, _STRICTNESS_HINT["standard"])


# ─────────────────────────────────────────────────────────────
# 初筛提示词:batch 批量打分
# ─────────────────────────────────────────────────────────────

QUICK_JUDGE_PROMPT = """\
你是学术论文查重专家。判断以下各片段是否与对应参考片段构成学术不端。

{segments_block}

判断规则：
- 文字重复度 > 70% → 抄袭
- 核心论点相同但句式完全重写 → 抄袭
- 通用学术表述（"研究表明""本文提出"）→ 正常
- 纯数字、公式、参考文献格式 → 正常

输出格式（严格按此，不要多余文字）：
{index_block}
"""


# 第二级：深度确认（qwen-plus）
DEEP_CONFIRM_PROMPT = """\
你是学术诚信审查专家。

待审查片段："{segment}"
疑似来源："{reference}"
所属章节：{section}

从字面相似度、语义相似度、改写程度、引用规范四个维度分析。

输出格式（严格 JSON，不要 markdown 代码块）：
{{"is_plagiarism": true/false, "confidence": 0-100, "rewrite_detected": true/false, "verdict": "直接抄袭/改写抄袭/正常引用/正常", "reason": "一句话说明"}}
"""


def build_quick_judge_prompt(segments: list) -> str:
    """
    segments: [{"index": 1, "text": "...", "reference": "..."}]
    """
    seg_lines = "\n".join(
        f'【片段{s["index"]}】待检测："{s["text"]}" | 参考："{s["reference"]}"'
        for s in segments
    )
    idx_lines = "\n".join(f'{s["index"]}: YES/NO' for s in segments)
    return QUICK_JUDGE_PROMPT.format(segments_block=seg_lines, index_block=idx_lines)


# ─────────────────────────────────────────────────────────────
# 改写建议(博士/期刊)
# ─────────────────────────────────────────────────────────────

REWRITE_ADVICE_PROMPT = """\
你是学术写作指导老师。对以下疑似重复片段,请给出{level_label}层次的改写建议。

原片段:
{segment}

疑似来源:{source}
相似度:{similarity:.0%}

要求:
1. 指出该片段的具体问题(直接引用 / 观点借用 / 方法复刻等)
2. 给出一句话改写思路
3. 建议添加的规范引用格式(GB/T 7714)

输出格式(严格 JSON,不要 markdown 代码块):
{{"issue":"问题简述","rewrite_tip":"一句改写思路","citation_template":"建议引用格式"}}
"""


JOURNAL_ADVICE_PROMPT = """\
你是期刊审稿专家。根据以下查重结果,给出这篇投稿的整体评价。

总重复率:{rate}%
高相似片段数:{high_count}
期刊红线:{red_line}%

要求:
1. 判断是否能送外审(通过 / 退修 / 直接 reject)
2. 指出 2-3 个最严重的问题区域
3. 给出修改优先级

输出格式(严格 JSON,不要 markdown 代码块):
{{"verdict":"通过/退修/reject","top_issues":["问题1","问题2"],"priority":"一句话优先级建议"}}
"""


def build_rewrite_advice_prompt(segment: str, source: str, similarity: float, level_label: str) -> str:
    return REWRITE_ADVICE_PROMPT.format(
        segment=segment,
        source=source,
        similarity=similarity,
        level_label=level_label,
    )


def build_journal_advice_prompt(rate: float, high_count: int, red_line: float) -> str:
    return JOURNAL_ADVICE_PROMPT.format(
        rate=rate,
        high_count=high_count,
        red_line=red_line,
    )
