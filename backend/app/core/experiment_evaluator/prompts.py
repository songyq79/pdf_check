"""
实验设计评审提示词。
参考 SKILL_experimental_design 的「毁掉研究的结构性错误清单」(Fisher 三原则:
随机化/重复/区组;以及伪重复、混杂、批次效应、别名、无对照、无曲率优化等)，
改写为「评审已有方案」的 JSON 提示词（方向与 SKILL 的「生成设计」相反）。
理工科限定。
"""

# 结构性错误清单（嵌入 prompt，引导逐项排查）
_FLAW_CHECKLIST = """请逐项排查以下结构性错误（这些错误事后分析无法补救，只能在设计阶段避免）：
1. 伪重复(pseudoreplication)：把同一单元的重复测量当独立重复（如 3 只鼠各测 100 个细胞，n 是 3 不是 300）
2. 混杂(confounding)：处理与某干扰因素绑定（如处理组全周一做、对照组全周二做 → 处理与日期混杂）
3. 随机化缺失/破坏：便利分组让混杂因素混入
4. 无恰当对照：缺并行对照/空白/盲法
5. 批次效应：样本未随机化/区组化跨批次处理（组学尤甚）
6. 孔板边缘/位置效应：蒸发与温度梯度，对照不应全放一列
7. 别名(aliasing)：低分辨率分式析因把主效应与交互混淆
8. 无曲率优化：两水平析因无法检出曲面最优，需响应面设计"""


def build_review_prompt(plan_text: str, discipline: str = "") -> str:
    return f"""你是一位严格的实验设计评审专家（{discipline or "理工科"}）。请评审以下实验方案（**评审、诊断、给建议，不要替学生重新设计整个实验**）。

{_FLAW_CHECKLIST}

【待评审的实验方案】
{plan_text}

请从两个维度打分（1-10 整数，先找问题再打分）：
- scientific_validity 科学性：随机化/对照/重复是否到位，能否支撑因果结论
- completeness 完整性：变量、样本量、流程、统计方法是否交代清楚、可复现

评审要求：
① 各分析结合方案的具体内容，禁止「设计较合理」这类空话。
② risks 列出技术/伦理/安全风险，每条标严重度(high/medium/low)。
③ detected_flaws 明确指出命中了上面清单的哪些结构性错误（没有则空数组）。
④ cost_estimate 粗估所需成本与时间。
⑤ methodology_suggestions 给可操作的改进建议。

请严格按以下 JSON 输出，不要输出任何其他文字：
{{"scientific_validity_score": 7, "completeness_score": 6, "scientific_validity": "...", "completeness": "...", "risks": [{{"type": "技术", "description": "...", "severity": "medium"}}], "detected_flaws": ["伪重复: ..."], "cost_estimate": "...", "methodology_suggestions": ["..."]}}"""


REVIEW_FALLBACK = {
    "scientific_validity_score": 5,
    "completeness_score": 5,
    "scientific_validity": "",
    "completeness": "",
    "risks": [],
    "detected_flaws": [],
    "cost_estimate": "",
    "methodology_suggestions": [],
}
