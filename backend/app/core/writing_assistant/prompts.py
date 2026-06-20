"""
高级写作辅助提示词。
参考 SKILL_scientific_writing 的写作原则（清晰/简洁/准确/客观、IMRAD、
学科术语规范），改写为「逐段给建议」的 JSON 提示词。
不改写原文，只标问题 + 给修改建议；按三类论文分化。
"""

_TYPE_FOCUS = {
    "humanities": "人文社科：关注论证严密性、概念准确、文献支撑、表述客观。",
    "science_engineering": "理工农医：关注表述精确、术语规范、数据/方法陈述清晰、避免主观夸大。",
    "arts": "艺术：关注理论与创作结合的表达、审美判断的清晰陈述、术语恰当。",
}


def build_writing_check_prompt(paragraph: str, paper_type: str = "humanities") -> str:
    focus = _TYPE_FOCUS.get(paper_type, _TYPE_FOCUS["humanities"])
    return f"""你是一位资深学术写作导师。请对以下论文段落给出改进建议（**只诊断、给建议，不要重写整段**）。

【学科侧重】{focus}

从四个维度检查，每个维度列出具体问题（没有问题就空数组）：
1. grammar 语法：主谓不一致、成分缺失、病句、标点
2. style 风格：口语化、冗余、主观夸大、术语不规范、被动/主动不当
3. logic 逻辑：句间跳跃、指代不清、段内矛盾、缺过渡
4. argument 论证：论点不明、论据不足、缺引用支撑、以偏概全

每条问题给出：引用的原文片段(excerpt) + 问题(issue) + 修改建议(suggestion)。
要求具体、可操作，禁止「表达不够流畅」这类空泛评价；建议要给出可直接采用的改法。

【待检查段落】
{paragraph}

请严格按以下 JSON 输出，不要输出任何其他文字：
{{"grammar": [{{"excerpt": "原文片段", "issue": "问题", "suggestion": "建议"}}], "style": [], "logic": [], "argument": [], "overall": "一句话总评"}}"""


WRITING_CHECK_FALLBACK = {
    "grammar": [],
    "style": [],
    "logic": [],
    "argument": [],
    "overall": "",
}
