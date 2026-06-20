"""
论文评价系统 - 提示词模板 V2.0

依据《山东省本科毕业论文(设计)抽检评议要素(试行)》设计。

核心原则：
1. 追问式提示词：要求 AI 引用原文具体内容举证，禁止泛泛而谈
2. 各维度按需取内容：不同维度只看最相关的部分，提升评价针对性
3. 明确禁止套话：在提示词里显式列出不允许出现的模板化表述
4. 评分锚定：先列问题再打分，给出扣分标准防止分数虚高
5. 三类论文差异：评议要素描述按类别区分

五个一级指标及权重：
  选题意义(10) + 写作安排(10) + 逻辑构建(20) + 专业能力(40) + 学术规范(20) = 100
"""

# ─────────────────────────────────────────────────────────────
# 三类论文的评议要素差异描述
# ─────────────────────────────────────────────────────────────

# 选题意义 - 价值导向差异
_VALUE_ORIENTATION = {
    "humanities": "符合党和国家社会科学与人文科学发展方向",
    "science_engineering": "顺应国内外科技发展趋势和创新精神",
    "arts": "符合我国社会主义精神文明建设和文化事业发展要求",
}

# 选题意义 - 选题目的差异
_TOPIC_PURPOSE = {
    "humanities": "面向所在专业领域学术问题或行业社会实际问题，有一定的理论或实用价值",
    "science_engineering": "面向所在专业领域学术问题或行业社会实际问题，有一定的理论或实用价值",
    "arts": "选题与艺术创作和实践紧密相连，面向所在专业领域学术问题或行业社会实际问题，有一定的理论或应用参考价值",
}

# 逻辑构建 - 内容组织差异
_CONTENT_ORG = {
    "humanities": "核心模块完备，层次分明，重点突出，详略得当",
    "science_engineering": "核心模块完备，层次分明，重点突出，详略得当",
    "arts": "核心模块完备，层次分明，重点突出，详略得当。鼓励结合自己的毕业创作(作品)进行写作。毕业设计内容有一定的实践可操作性、艺术性与思想深度",
}

# 逻辑构建 - 逻辑结构差异
_LOGIC_STRUCTURE = {
    "humanities": "概念准确，理论运用合理，研究(设计)路径合理，论点鲜明，论据确凿，论证严谨，结论可靠",
    "science_engineering": "研究（设计）路径合理，论点鲜明，论据确凿，论证充分，达到所在专业领域要求",
    "arts": "概念准确，理论运用合理，论点鲜明，论据确凿，论证严谨，结论可靠",
}

# 专业能力 - 文献调研差异
_LIT_REVIEW = {
    "humanities": "综合分析国内外文献，追踪本领域研究现状或行业动态，能支撑该论文(设计)的选题",
    "science_engineering": "综合分析国内外文献，追踪本领域研究现状或行业动态，关注学科及本领域前沿，能支撑该论文(设计)的选题",
    "arts": "具有一定的文献资料查阅、整理、分析能力，追踪本领域研究现状或行业动态，能支撑该论文(设计)的选题",
}

# 专业能力 - 综合应用知识差异
_KNOWLEDGE_APP = {
    "humanities": "将相关领域的基础理论、专业知识合理应用到研究(设计)工作中，能体现所在专业领域的能力和素养",
    "science_engineering": "将相关领域的基础理论、专业知识合理应用到研究（设计）工作中，能体现所在专业领域的能力和素养",
    "arts": "将相关领域的基础理论、专业知识合理应用到毕业设计（创作）工作中，能体现所在专业领域的能力和素养",
}

# 专业能力 - 分析解决问题差异
_PROBLEM_SOLVING = {
    "humanities": "掌握基础的专业知识和研究方法，善于发现问题、分析问题，体现出一定的解决本专业领域问题的能力和素养",
    "science_engineering": "运用专业知识，采取恰当的研究（设计）方法、路径开展研究（设计），善于发现问题、分析问题，具备解决实际问题的能力和素养",
    "arts": "掌握基础的专业知识和研究方法，进行理论研究（艺术创作与实践），善于发现问题、分析问题，体现出一定的解决本专业领域问题的能力和水平",
}

# 专业能力 - 创新能力差异
_INNOVATION = {
    "humanities": "坚持问题导向，观点新颖，体现出较强的创新意识，或对实践具有一定指导意义",
    "science_engineering": "观点新颖，体现出较强的创新意识，或对实践具有一定指导意义",
    "arts": "体现作者的独立思考，内容有一定的特色或新意，或对实践具有一定指导意义",
}

_TYPE_NAMES = {
    "humanities": "人文社科类（第Ⅰ类）",
    "science_engineering": "理工农医类（第Ⅱ类）",
    "arts": "艺术类（第Ⅲ类）",
}

# ─────────────────────────────────────────────────────────────
# 类型评审侧重说明（嵌入每个维度的 prompt 中，引导 AI 按类型差异化评分）
# ─────────────────────────────────────────────────────────────

_TYPE_FOCUS = {
    "humanities": (
        "【评审侧重（人文社科类）】\n"
        "本论文属于人文社科类，评审时应重点关注：\n"
        "- 理论框架是否扎实，概念界定是否清晰准确\n"
        "- 论证逻辑是否严密，是否有充分的文献支撑\n"
        "- 研究方法（如问卷调查、案例分析、比较研究等）是否规范\n"
        "- 对社会现实问题的关照度和理论解释力\n"
        "如果论文在理论深度、文献综述、论证严密性方面表现不佳，应显著扣分。"
    ),
    "science_engineering": (
        "【评审侧重（理工农医类）】\n"
        "本论文属于理工农医类，评审时应重点关注：\n"
        "- 实验/研究设计是否科学合理，是否有对照组或控制变量\n"
        "- 数据采集、处理和分析方法是否恰当（统计方法、算法选择等）\n"
        "- 研究结果是否有数据支撑，图表是否规范\n"
        "- 技术路线是否清晰，是否具有可重复性\n"
        "如果论文缺乏实验数据支撑、研究方法不科学、技术细节不充分，应显著扣分。"
    ),
    "arts": (
        "【评审侧重（艺术类）】\n"
        "本论文属于艺术类，评审时应重点关注：\n"
        "- 理论研究与艺术创作/实践的结合程度\n"
        "- 是否体现作者的独立审美判断和创作思考\n"
        "- 对艺术作品、流派、技法的分析是否有深度\n"
        "- 毕业设计/创作的实践可操作性和艺术性\n"
        "如果论文脱离艺术实践、缺乏创作体验的融入、纯粹堆砌理论而无个人见解，应显著扣分。"
    ),
}


# ─────────────────────────────────────────────────────────────
# 选题意义（10分）：标题 + 摘要 + 大纲 + 第一章摘要
# ─────────────────────────────────────────────────────────────

def _build_topic_significance_prompt(paper_struct: dict, paper_type: str) -> str:
    value_orient = _VALUE_ORIENTATION.get(paper_type, _VALUE_ORIENTATION["humanities"])
    topic_purpose = _TOPIC_PURPOSE.get(paper_type, _TOPIC_PURPOSE["humanities"])
    type_name = _TYPE_NAMES.get(paper_type, "")

    type_focus = _TYPE_FOCUS.get(paper_type, _TYPE_FOCUS["humanities"])

    return f"""你是一位严格的学术论文评审专家。请对以下{type_name}论文的「选题意义」进行评价。

{type_focus}

【论文标题】
{paper_struct.get("title", "（未提取到）")}

【摘要】
{paper_struct.get("abstract", "（未提取到）")}

【论文章节大纲】
{paper_struct.get("outline", "（未提取到）")}

【引言/第一章内容摘要】
{paper_struct.get("chapter_summaries", "（未提取到）")[:2000]}

---
评议标准（山东省抽检标准）：
1. 价值导向：体现立德树人要求，符合党和国家方针政策和法律法规，符合社会主义核心价值观，{value_orient}。
2. 选题目的与意义：符合专业培养目标，体现综合训练基本要求；{topic_purpose}。

评分锚定（先找问题再打分）：
- 90-100分：选题紧密结合专业前沿或重大现实问题，研究意义论述充分且有说服力
- 75-89分：选题有一定价值，研究意义论述基本清楚但不够深入
- 60-74分：选题较为常规，研究意义论述笼统或缺乏针对性
- 60分以下：选题偏离专业方向，或研究意义论述严重不足

评价要求：
① 每条优点和问题都必须引用论文中的具体内容作为依据，不允许写"选题合理"、"具有研究意义"等空洞套话
② 必须具体分析选题与专业领域的关联度，指出选题的理论或实用价值体现在哪里
③ 先列出所有问题，再根据问题严重程度打分

请按以下 JSON 格式输出，不要输出任何其他文字：
{{"score": 85, "strengths": ["基于原文的具体优点"], "weaknesses": ["具体问题"], "suggestions": ["可操作的建议"]}}"""


# ─────────────────────────────────────────────────────────────
# 写作安排（10分）：大纲 + 各章摘要 + 全文字数
# ─────────────────────────────────────────────────────────────

def _build_writing_arrangement_prompt(paper_struct: dict, paper_type: str) -> str:
    type_name = _TYPE_NAMES.get(paper_type, "")
    type_focus = _TYPE_FOCUS.get(paper_type, _TYPE_FOCUS["humanities"])

    return f"""你是一位严格的学术论文评审专家。请对以下{type_name}论文的「写作安排」进行评价。

{type_focus}

【论文标题】
{paper_struct.get("title", "（未提取到）")}

【论文章节大纲】
{paper_struct.get("outline", "（未提取到）")}

【各章节内容摘要】
{paper_struct.get("chapter_summaries", "（未提取到）")}

【全文大致字数】
{len(paper_struct.get("language_sample", "")) * 3} 字（估算）

---
评议标准（山东省抽检标准）：
1. 写作形式：写作形式符合专业特点和选题需要。
2. 工作量：工作量饱满，能反映出学生的综合能力培养过程。

评分锚定（先找问题再打分）：
- 90-100分：写作形式完全符合专业规范，章节安排合理，工作量充实饱满
- 75-89分：写作形式基本规范，工作量适中，个别章节安排可优化
- 60-74分：写作形式有明显不足，或工作量偏少，部分章节内容单薄
- 60分以下：写作形式严重不规范，或工作量明显不足

评价要求：
① 从大纲结构判断各章节篇幅是否均衡，有无头重脚轻或虎头蛇尾
② 分析写作形式是否符合该专业的论文规范（如是否有文献综述、研究方法、数据分析等必要章节）
③ 根据章节数量和内容摘要判断工作量是否饱满
④ 禁止出现"结构完整"、"安排合理"等不加分析的空洞评价

请按以下 JSON 格式输出，不要输出任何其他文字：
{{"score": 80, "strengths": ["基于原文的具体优点"], "weaknesses": ["具体问题"], "suggestions": ["可操作的建议"]}}"""


# ─────────────────────────────────────────────────────────────
# 逻辑构建（20分）：大纲 + 各章摘要 + 结论
# ─────────────────────────────────────────────────────────────

def _build_logic_construction_prompt(paper_struct: dict, paper_type: str) -> str:
    content_org = _CONTENT_ORG.get(paper_type, _CONTENT_ORG["humanities"])
    logic_struct = _LOGIC_STRUCTURE.get(paper_type, _LOGIC_STRUCTURE["humanities"])
    type_name = _TYPE_NAMES.get(paper_type, "")
    type_focus = _TYPE_FOCUS.get(paper_type, _TYPE_FOCUS["humanities"])

    return f"""你是一位严格的学术论文评审专家。请对以下{type_name}论文的「逻辑构建」进行评价。

{type_focus}

【论文标题】
{paper_struct.get("title", "（未提取到）")}

【论文章节大纲】
{paper_struct.get("outline", "（未提取到）")}

【各章节内容摘要】
{paper_struct.get("chapter_summaries", "（未提取到）")}

【结论部分】
{paper_struct.get("conclusion", "（未提取到）")}

---
评议标准（山东省抽检标准）：
1. 内容组织：{content_org}。
2. 逻辑结构：{logic_struct}。

评分锚定（先找问题再打分）：
- 90-100分：逻辑链完整自洽，各章递进关系清晰，论证严密，结论有力
- 75-89分：整体逻辑通顺，个别环节论证不够充分或存在小的逻辑跳跃
- 60-74分：逻辑链有明显断裂，部分章节之间缺乏衔接，论证不够严谨
- 60分以下：逻辑混乱，章节之间缺乏内在联系，论证严重不足

评价要求：
① 结合章节大纲和各章内容，评判"研究问题→研究方法→分析过程→结论"这条逻辑链是否完整自洽
② 找出逻辑断裂点：哪个环节论证不充分、跳跃、或与其他章节矛盾，请具体说明
③ 分析各章节之间的递进关系是否合理，找出脱节之处
④ 禁止出现"逻辑清晰"、"结构合理"等不加分析的空洞评价

请按以下 JSON 格式输出，不要输出任何其他文字：
{{"score": 78, "strengths": ["结合具体章节的优点"], "weaknesses": ["具体章节+具体逻辑问题"], "suggestions": ["针对具体逻辑断裂的修改建议"]}}"""


# ─────────────────────────────────────────────────────────────
# 专业能力（40分）：大纲 + 各章摘要 + 参考文献 + 结论 + 语言样本
# 包含4个二级指标，要求分别评述
# ─────────────────────────────────────────────────────────────

def _build_professional_ability_prompt(paper_struct: dict, paper_type: str) -> str:
    lit_review = _LIT_REVIEW.get(paper_type, _LIT_REVIEW["humanities"])
    knowledge_app = _KNOWLEDGE_APP.get(paper_type, _KNOWLEDGE_APP["humanities"])
    problem_solving = _PROBLEM_SOLVING.get(paper_type, _PROBLEM_SOLVING["humanities"])
    innovation = _INNOVATION.get(paper_type, _INNOVATION["humanities"])
    type_name = _TYPE_NAMES.get(paper_type, "")
    type_focus = _TYPE_FOCUS.get(paper_type, _TYPE_FOCUS["humanities"])

    return f"""你是一位严格的学术论文评审专家。请对以下{type_name}论文的「专业能力」进行评价。

{type_focus}

【论文标题】
{paper_struct.get("title", "（未提取到）")}

【论文章节大纲】
{paper_struct.get("outline", "（未提取到）")}

【各章节内容摘要】
{paper_struct.get("chapter_summaries", "（未提取到）")}

【结论部分】
{paper_struct.get("conclusion", "（未提取到）")}

【参考文献（前20条）】
{paper_struct.get("references", "（未提取到）")}

【正文样本（从不同章节抽取）】
{paper_struct.get("language_sample", "（未提取到）")[:3000]}

---
评议标准（山东省抽检标准，本维度占40分，是最重要的维度）：

本维度包含4个二级指标，请逐一评述：

【二级指标1：文献调研能力】
{lit_review}

【二级指标2：综合应用知识能力】
{knowledge_app}

【二级指标3：分析解决问题能力】
{problem_solving}

【二级指标4：创新能力】
{innovation}

评分锚定（先找问题再打分，综合4个子项给出总分）：
- 90-100分：文献调研全面深入，专业知识运用娴熟，研究方法得当，有明显创新点
- 75-89分：文献调研较充分，专业知识运用基本合理，研究方法可行，有一定新意
- 60-74分：文献调研不够全面，专业知识运用有欠缺，研究方法较为简单，创新不足
- 60分以下：文献调研严重不足，专业知识运用有明显错误，缺乏有效的研究方法

评价要求：
① 必须对4个二级指标分别评述，在 strengths/weaknesses 中标注属于哪个子项
② 文献调研：分析参考文献的数量、质量、时效性，是否覆盖核心文献
③ 综合应用：从正文样本中找出专业知识运用的具体例子，判断是否合理
④ 分析解决问题：评价研究方法是否恰当，分析过程是否严谨
⑤ 创新能力：结合论文具体研究对象，指出创新点或不足，不允许说"有一定创新性"
⑥ 禁止出现"研究具有一定意义"、"具有理论与实践价值"等套话

请按以下 JSON 格式输出，不要输出任何其他文字：
{{"score": 75, "strengths": ["[文献调研] 具体优点", "[综合应用] 具体优点"], "weaknesses": ["[分析解决问题] 具体问题", "[创新能力] 具体问题"], "suggestions": ["针对具体子项的改进建议"]}}"""


# ─────────────────────────────────────────────────────────────
# 学术规范（20分）：大纲 + 参考文献 + 引用标注抽样 + 语言样本
# ─────────────────────────────────────────────────────────────

def _build_academic_standard_prompt(paper_struct: dict, paper_type: str) -> str:
    type_name = _TYPE_NAMES.get(paper_type, "")
    type_focus = _TYPE_FOCUS.get(paper_type, _TYPE_FOCUS["humanities"])

    return f"""你是一位熟悉 GB/T 7714 标准的学术规范专家。请对以下{type_name}论文的「学术规范」进行评价。

{type_focus}

【论文标题】
{paper_struct.get("title", "（未提取到）")}

【论文章节大纲】
{paper_struct.get("outline", "（未提取到）")}

【参考文献列表】
{paper_struct.get("references", "（未提取到）")}

【正文引用标注抽样（含上下文）】
{paper_struct.get("citation_samples", "（未提取到）")}

【正文样本（从不同章节抽取）】
{paper_struct.get("language_sample", "（未提取到）")[:2000]}

---
评议标准（山东省抽检标准）：
1. 行文规范：文字表达、书写格式、图表(图纸)、公式符号、缩略词等方面符合通行学术规范。
2. 引用规范：在资料引证、参考文献等方面符合通行学术规范和知识产权相关规定。

评分锚定（先找问题再打分）：
- 90-100分：行文格式完全规范，参考文献格式正确，引用标注准确无误
- 75-89分：行文基本规范，参考文献格式有少量错误，引用标注基本正确
- 60-74分：行文规范有明显不足，参考文献格式错误较多，引用标注有遗漏
- 60分以下：行文严重不规范，参考文献格式混乱，引用标注问题严重

评价要求：
① 逐条检查参考文献格式，指出具体哪几条存在什么格式问题（如作者格式、年份位置、期刊名、页码格式等）
② 从正文样本中找出行文规范问题（术语不统一、格式不一致等），直接引用原文
③ 从引用标注抽样中，判断正文引用是否与参考文献列表对应
④ 分析文献的时效性（近5年文献占比）和权威性
⑤ 禁止出现"参考文献较为丰富"、"引用较为规范"等模糊评价

请按以下 JSON 格式输出，不要输出任何其他文字：
{{"score": 82, "strengths": ["基于实际文献列表的具体优点"], "weaknesses": ["具体条目+具体格式问题"], "suggestions": ["针对具体问题的修正建议"]}}"""


# ─────────────────────────────────────────────────────────────
# 学术诚信风险提示（不计分，仅做风险提醒）
# ─────────────────────────────────────────────────────────────

PROMPT_INTEGRITY_CHECK = """你是一位学术诚信审查专家。请对以下论文进行初步的学术诚信风险评估。

【论文标题】
{title}

【正文样本（从不同章节抽取）】
{language_sample}

【参考文献列表】
{references}

---
注意：这不是最终的学术不端判定，仅做初步风险提示。

请检查以下方面：
1. 正文样本中是否存在前后写作风格突变（可能暗示拼凑或代写）
2. 是否有大段描述性文字缺少引用标注（可能存在未标注的引用）
3. 参考文献是否看起来真实合理（有无明显编造的迹象）

请按以下 JSON 格式输出，不要输出任何其他文字：
{{"has_risk": false, "risk_items": ["具体风险描述（如有）"], "note": "总体评估说明"}}"""


# ─────────────────────────────────────────────────────────────
# 维度配置
# ─────────────────────────────────────────────────────────────

# 维度权重（满分100）
DIMENSION_WEIGHTS = {
    "topic_significance":    10,
    "writing_arrangement":   10,
    "logic_construction":    20,
    "professional_ability":  40,
    "academic_standard":     20,
}

# 维度中文名
DIMENSION_NAMES = {
    "topic_significance":    "选题意义",
    "writing_arrangement":   "写作安排",
    "logic_construction":    "逻辑构建",
    "professional_ability":  "专业能力",
    "academic_standard":     "学术规范",
}

# 各维度的 prompt 构建函数
_PROMPT_BUILDERS = {
    "topic_significance":    _build_topic_significance_prompt,
    "writing_arrangement":   _build_writing_arrangement_prompt,
    "logic_construction":    _build_logic_construction_prompt,
    "professional_ability":  _build_professional_ability_prompt,
    "academic_standard":     _build_academic_standard_prompt,
}

# 各维度需要的 paper_struct 字段
DIMENSION_FIELDS = {
    "topic_significance":    ["title", "abstract", "outline", "chapter_summaries"],
    "writing_arrangement":   ["title", "outline", "chapter_summaries", "language_sample"],
    "logic_construction":    ["title", "outline", "chapter_summaries", "conclusion"],
    "professional_ability":  ["title", "outline", "chapter_summaries", "conclusion", "references", "language_sample"],
    "academic_standard":     ["title", "outline", "references", "citation_samples", "language_sample"],
}


# ─────────────────────────────────────────────────────────────
# 公共接口
# ─────────────────────────────────────────────────────────────

def get_prompt(dimension: str, paper_struct: dict, paper_type: str = "humanities") -> str:
    """
    获取指定维度的提示词。

    Args:
        dimension: 维度标识（如 topic_significance）
        paper_struct: 论文结构化数据
        paper_type: 论文类别（humanities / science_engineering / arts）
    """
    builder = _PROMPT_BUILDERS.get(dimension)
    if builder is None:
        raise ValueError(f"未知的评价维度: {dimension}")
    return builder(paper_struct, paper_type)


def get_integrity_prompt(paper_struct: dict) -> str:
    """获取学术诚信风险检查的提示词"""
    return PROMPT_INTEGRITY_CHECK.format(
        title=paper_struct.get("title", "（未提取到）"),
        language_sample=paper_struct.get("language_sample", "（未提取到）")[:3000],
        references=paper_struct.get("references", "（未提取到）"),
    )


def get_dimension_name(dimension: str) -> str:
    return DIMENSION_NAMES.get(dimension, dimension)


def get_all_dimensions() -> list:
    return list(_PROMPT_BUILDERS.keys())


def get_dimension_weight(dimension: str) -> int:
    return DIMENSION_WEIGHTS.get(dimension, 0)


def get_type_name(paper_type: str) -> str:
    return _TYPE_NAMES.get(paper_type, "未知类别")
