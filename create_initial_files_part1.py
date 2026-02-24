"""
生成核心代码文件脚本
一次性创建所有核心代码文件的内容
"""

from pathlib import Path

# 定义所有要生成的文件及其内容
FILES_CONTENT = {
    "backend/app/core/evaluator/prompts.py": '''"""
论文评价系统 - 提示词模板
包含4个评价维度的提示词模板，硬编码在系统中
"""

# 学术规范性评价提示词
PROMPT_ACADEMIC_STANDARD = """你是一位资深的学术专家和论文评审专家。请对以下论文的学术规范性进行评价。

论文标题：{title}
论文内容：
{content}

请从以下角度进行评价：
1. 论文结构完整性：摘要、关键词、引言、研究方法、结果、讨论、结论、参考文献等部分是否齐全
2. 学术用语规范性：是否使用规范的学术术语，避免口语化表达
3. 格式规范性：标题层级、图表标注、公式编号等是否规范

请按以下JSON格式输出：
{{
  "score": 85,
  "strengths": ["优点1", "优点2", "优点3"],
  "weaknesses": ["问题1", "问题2"],
  "suggestions": ["改进建议1", "改进建议2", "改进建议3"]
}}

请确保输出是严格的JSON格式，不要包含其他文字说明。"""


# 逻辑与创新性评价提示词
PROMPT_LOGIC_INNOVATION = """你是一位资深的学术专家。请对以下论文的逻辑性和创新性进行评价。

论文标题：{title}
论文内容：
{content}

请从以下角度进行评价：
1. 论证逻辑：研究问题-方法-结果-结论的逻辑链条是否清晰严密
2. 研究创新性：研究角度、方法或结论是否有新意，是否对现有研究有所突破
3. 论据充分性：数据、案例、文献支撑是否充分有力

请按以下JSON格式输出：
{{
  "score": 80,
  "strengths": ["优点1", "优点2", "优点3"],
  "weaknesses": ["问题1", "问题2"],
  "suggestions": ["改进建议1", "改进建议2", "改进建议3"]
}}

请确保输出是严格的JSON格式，不要包含其他文字说明。"""


# 语言质量评价提示词
PROMPT_LANGUAGE_QUALITY = """你是一位资深的学术专家。请对以下论文的语言质量进行评价。

论文标题：{title}
论文内容：
{content}

请从以下角度进行评价：
1. 学术用语准确性：专业术语使用是否准确、规范
2. 表达清晰度：语句是否通顺，逻辑是否清晰，是否存在歧义
3. 语言简洁性：是否避免冗余表达，文字是否精炼

请按以下JSON格式输出：
{{
  "score": 88,
  "strengths": ["优点1", "优点2", "优点3"],
  "weaknesses": ["问题1", "问题2"],
  "suggestions": ["改进建议1", "改进建议2", "改进建议3"]
}}

请确保输出是严格的JSON格式，不要包含其他文字说明。"""


# 文献引用规范性评价提示词
PROMPT_CITATION_STANDARD = """你是一位资深的学术专家。请对以下论文的文献引用规范性进行评价。

论文标题：{title}
论文内容：
{content}

请从以下角度进行评价：
1. 参考文献格式：是否符合学术规范（如GB/T 7714、APA等），格式是否统一
2. 引用合理性：引用的文献是否权威、相关，是否有遗漏重要文献
3. 引用标注：正文中的引用标注是否准确、完整

请按以下JSON格式输出：
{{
  "score": 82,
  "strengths": ["优点1", "优点2", "优点3"],
  "weaknesses": ["问题1", "问题2"],
  "suggestions": ["改进建议1", "改进建议2", "改进建议3"]
}}

请确保输出是严格的JSON格式，不要包含其他文字说明。"""


# 提示词模板映射
PROMPT_TEMPLATES = {
    "academic_standard": PROMPT_ACADEMIC_STANDARD,
    "logic_innovation": PROMPT_LOGIC_INNOVATION,
    "language_quality": PROMPT_LANGUAGE_QUALITY,
    "citation_standard": PROMPT_CITATION_STANDARD,
}


# 维度名称映射（中文）
DIMENSION_NAMES = {
    "academic_standard": "学术规范性",
    "logic_innovation": "逻辑与创新性",
    "language_quality": "语言质量",
    "citation_standard": "文献引用规范性",
}


def get_prompt(dimension: str, title: str, content: str) -> str:
    """
    获取指定维度的提示词

    :param dimension: 评价维度
    :param title: 论文标题
    :param content: 论文内容
    :return: 格式化后的提示词
    """
    if dimension not in PROMPT_TEMPLATES:
        raise ValueError(f"未知的评价维度: {dimension}")

    template = PROMPT_TEMPLATES[dimension]
    return template.format(title=title, content=content)


def get_dimension_name(dimension: str) -> str:
    """获取维度的中文名称"""
    return DIMENSION_NAMES.get(dimension, dimension)


def get_all_dimensions() -> list:
    """获取所有评价维度"""
    return list(PROMPT_TEMPLATES.keys())
''',

    # 其他文件内容将在下面继续...
}


def generate_files():
    """生成所有核心文件"""
    base_path = Path(__file__).parent
    created_count = 0

    for file_path, content in FILES_CONTENT.items():
        full_path = base_path / file_path

        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        full_path.write_text(content, encoding='utf-8')
        print(f"[OK] 已创建: {file_path}")
        created_count += 1

    print(f"\n===== 完成 =====")
    print(f"共生成 {created_count} 个核心代码文件")
    print("\n接下来:")
    print("  1. 进入backend目录: cd backend")
    print("  2. 创建虚拟环境: python -m venv venv")
    print("  3. 激活虚拟环境: venv\\Scripts\\activate")
    print("  4. 安装依赖: pip install -r requirements.txt")
    print("  5. 配置.env文件: cp .env.example .env")
    print("  6. 启动服务: python -m app.main")


if __name__ == "__main__":
    generate_files()
