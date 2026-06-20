"""
选题评估提示词。
参考 SKILL_hypothesis 方法论（可证伪性/解释力/新颖性框架），
改写为返回 JSON 的提示词；评分口径用 PRD 定的「创新性/可行性/重要性」。
按 humanities / science_engineering / arts 三类论文分化。
所有 prompt 配 fallback dict，经 ai_client.parse_json_response 解析。
"""

# ── 三类论文评审侧重（嵌入评估 prompt）────────────────────────
_TYPE_FOCUS = {
    "humanities": (
        "本选题属人文社科类，评估时重点关注：理论框架的扎实度、概念界定的清晰度、"
        "对社会现实问题的关照度、研究方法（案例/比较/质性等）的适配性。"
    ),
    "science_engineering": (
        "本选题属理工农医类，评估时重点关注：实验/技术路线的可行性、"
        "数据获取与方法的科学性、是否具备可重复性、技术指标的先进性。"
    ),
    "arts": (
        "本选题属艺术类，评估时重点关注：理论研究与艺术创作/实践的结合度、"
        "作者独立审美判断、作品/技法分析深度、创作的可操作性与艺术性。"
    ),
}

_TYPE_NAMES = {
    "humanities": "人文社科类",
    "science_engineering": "理工农医类",
    "arts": "艺术类",
}


# ── Step 1：选题解析，提关键词 + 检索 query ──────────────────

def build_topic_extraction_prompt(question: str, description: str,
                                  discipline: str, degree_level: str) -> str:
    return f"""你是一位学术选题分析专家。请分析以下研究选题，提炼核心概念，并生成用于检索相关文献的查询词。

【学科】{discipline or "未指定"}
【学位阶段】{degree_level or "未指定"}
【拟研究问题】
{question or "（未填写）"}
【研究方向描述】
{description or "（未填写）"}

要求：
1. 用一句话概括该选题的研究核心。
2. 提炼 5-8 个相关关键词（中文为主，专业术语可中英并列）。
3. 生成 3-5 条用于学术数据库检索的查询词（中英文混合，覆盖核心概念，便于检索到真实相关论文）。

请严格按以下 JSON 输出，不要输出任何其他文字：
{{"core_summary": "选题研究核心一句话", "related_keywords": ["关键词1", "关键词2"], "search_queries": ["query1", "english query 2"]}}"""


EXTRACTION_FALLBACK = {
    "core_summary": "",
    "related_keywords": [],
    "search_queries": [],
}


# ── Step 3：基于检索到的真实文献做 RAG 评估 ──────────────────

def _format_papers_for_prompt(papers: list, limit: int = 8) -> str:
    """把检索到的 CandidatePaper（或同结构 dict）拼成 prompt 文献清单。"""
    if not papers:
        return "（未检索到相关文献，请基于学科常识审慎评估，勿编造具体文献）"
    lines = []
    for i, p in enumerate(papers[:limit], 1):
        title = _attr(p, "title")
        year = _attr(p, "year")
        abstract = (_attr(p, "abstract") or "")[:300]
        lines.append(f"{i}. {title}（{year}）\n   摘要: {abstract}")
    return "\n".join(lines)


def _attr(obj, key, default=""):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def build_evaluation_prompt(question: str, description: str, discipline: str,
                            degree_level: str, papers: list,
                            paper_type: str = "humanities") -> str:
    type_focus = _TYPE_FOCUS.get(paper_type, _TYPE_FOCUS["humanities"])
    type_name = _TYPE_NAMES.get(paper_type, "")
    papers_block = _format_papers_for_prompt(papers)

    return f"""你是一位严格的{type_name}学位论文选题评审专家。请基于「下方检索到的真实相关文献」评估该选题。

【评审侧重】
{type_focus}

【学科】{discipline or "未指定"}　【学位阶段】{degree_level or "未指定"}
【拟研究问题】
{question or "（未填写）"}
【研究方向描述】
{description or "（未填写）"}

【已检索到的相关文献（务必据此判断选题与现有研究的差异，禁止编造文献）】
{papers_block}

请从三个维度打分（1-10 整数，先找问题再打分）：
- 创新性 innovation：与上述已有文献相比，本选题的新意/差异有多大？
- 可行性 feasibility：以该学位阶段的资源/时间/方法，能否完成？
- 重要性 importance：该选题的理论或实用价值有多大？

评价要求：
① 各维度分析必须结合上方真实文献或选题本身的具体内容，禁止"具有创新性""有研究价值"等空话。
② 创新点与挑战要具体可操作。
③ 若文献为空，明确说明"未检索到直接相关文献"，不得编造论文标题或作者。

请严格按以下 JSON 输出，不要输出任何其他文字：
{{"innovation_score": 7, "feasibility_score": 8, "importance_score": 6, "innovation_analysis": "...", "feasibility_analysis": "...", "importance_analysis": "...", "key_novelties": ["..."], "technical_challenges": ["..."], "improvement_suggestions": ["..."]}}"""


EVALUATION_FALLBACK = {
    "innovation_score": 5,
    "feasibility_score": 5,
    "importance_score": 5,
    "innovation_analysis": "",
    "feasibility_analysis": "",
    "importance_analysis": "",
    "key_novelties": [],
    "technical_challenges": [],
    "improvement_suggestions": [],
}


def get_type_name(paper_type: str) -> str:
    return _TYPE_NAMES.get(paper_type, "未知类别")
