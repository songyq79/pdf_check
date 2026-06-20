# backend/app/core/formatter/structure_analyzer.py
"""
智能论文结构识别器
支持多种识别策略：关键词、模式匹配、样式分析、AI识别
"""

from docx import Document
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from loguru import logger


class SectionType(Enum):
    """章节类型枚举"""
    TITLE = "title"                    # 论文标题
    AUTHOR = "author"                  # 作者
    ABSTRACT_CN = "abstract_cn"        # 中文摘要
    ABSTRACT_EN = "abstract_en"        # 英文摘要
    KEYWORDS_CN = "keywords_cn"        # 中文关键词
    KEYWORDS_EN = "keywords_en"        # 英文关键词
    TOC = "toc"                        # 目录
    CHAPTER = "chapter"                # 章
    SECTION_1 = "section_1"            # 一级节
    SECTION_2 = "section_2"            # 二级节
    SECTION_3 = "section_3"            # 三级节
    FIGURE = "figure"                  # 图
    TABLE = "table"                    # 表
    FORMULA = "formula"                # 公式
    REFERENCE = "references"           # 参考文献
    APPENDIX = "appendix"              # 附录
    ACKNOWLEDGEMENT = "acknowledgement" # 致谢
    BODY = "body"                      # 正文
    UNKNOWN = "unknown"                # 未知


@dataclass
class SectionInfo:
    """章节信息"""
    index: int                         # 段落索引
    type: SectionType                  # 章节类型
    text: str                          # 文本内容
    level: int = 0                     # 层级（0=顶级）
    confidence: float = 1.0            # 置信度
    method: str = "unknown"            # 识别方法
    numbering: Optional[str] = None    # 编号
    parent: Optional[int] = None       # 父节点索引
    children: List[int] = field(default_factory=list)  # 子节点索引


class StructureAnalyzer:
    """
    智能结构识别器

    识别策略（按优先级）：
    1. 关键词匹配（最高优先级）
    2. 编号模式匹配
    3. 样式分析
    4. 格式特征分析
    5. AI辅助识别（可选）
    """

    # 关键词配置（预编译正则，避免每个段落重复编译）
    # 所有模式加 ^ 锚点，防止正文中包含这些词的句子被误判为章节标题
    KEYWORDS = {
        SectionType.ABSTRACT_CN: [
            re.compile(r"^摘\s*要"), re.compile(r"^内容摘要"), re.compile(r"^中文摘要"), re.compile(r"^论文摘要")
        ],
        SectionType.ABSTRACT_EN: [
            re.compile(r"^Abstract", re.IGNORECASE), re.compile(r"^Summary", re.IGNORECASE)
        ],
        SectionType.KEYWORDS_CN: [
            re.compile(r"^关键词"), re.compile(r"^关键字"), re.compile(r"^主题词")
        ],
        SectionType.KEYWORDS_EN: [
            re.compile(r"^Keywords?", re.IGNORECASE), re.compile(r"^Key\s+words?", re.IGNORECASE), re.compile(r"^Index\s+terms?", re.IGNORECASE)
        ],
        SectionType.TOC: [
            re.compile(r"^目\s*录"), re.compile(r"^Table\s+of\s+Contents", re.IGNORECASE), re.compile(r"^Contents$", re.IGNORECASE)
        ],
        SectionType.CHAPTER: [
            re.compile(r"^第.{1,3}章"), re.compile(r"^Chapter\s+\d+", re.IGNORECASE)
        ],
        SectionType.REFERENCE: [
            re.compile(r"^参考文献"), re.compile(r"^References?$", re.IGNORECASE), re.compile(r"^Bibliography$", re.IGNORECASE), re.compile(r"^引用文献")
        ],
        SectionType.APPENDIX: [
            re.compile(r"^附\s*录"), re.compile(r"^Appendix", re.IGNORECASE), re.compile(r"^附件")
        ],
        SectionType.ACKNOWLEDGEMENT: [
            re.compile(r"^致\s*谢"), re.compile(r"^Acknowledgements?", re.IGNORECASE), re.compile(r"^谢辞")
        ]
    }

    # 编号模式（预编译）
    PATTERNS = {
        SectionType.CHAPTER: [
            re.compile(r"^第[一二三四五六七八九十百千]+章"),
            re.compile(r"^第\d+章"),
            re.compile(r"^Chapter\s+\d+", re.IGNORECASE),
        ],
        SectionType.SECTION_1: [
            re.compile(r"^\d+\s+"),                    # "1 引言"
            re.compile(r"^\d+\.\s+"),                  # "1. 引言"
            re.compile(r"^第[一二三四五六七八九十]+节"),
        ],
        SectionType.SECTION_2: [
            re.compile(r"^\d+\.\d+\s+"),               # "1.1 背景"
            re.compile(r"^\d+\.\d+\.\s+"),
        ],
        SectionType.SECTION_3: [
            re.compile(r"^\d+\.\d+\.\d+\s+"),          # "1.1.1 问题"
            re.compile(r"^\d+\.\d+\.\d+\.\s+"),
        ],
        SectionType.FIGURE: [
            re.compile(r"^图\s*\d+"),
            re.compile(r"^Figure\s+\d+", re.IGNORECASE),
        ],
        SectionType.TABLE: [
            re.compile(r"^表\s*\d+"),
            re.compile(r"^Table\s+\d+", re.IGNORECASE),
        ]
    }

    # 样式映射（Word内置样式）
    STYLE_MAP = {
        "Title": SectionType.TITLE,
        "Heading 1": SectionType.CHAPTER,
        "Heading 2": SectionType.SECTION_1,
        "Heading 3": SectionType.SECTION_2,
        "Heading 4": SectionType.SECTION_3,
        "标题": SectionType.TITLE,
        "标题 1": SectionType.CHAPTER,
        "标题 2": SectionType.SECTION_1,
        "标题 3": SectionType.SECTION_2,
    }

    def __init__(self, use_ai: bool = False, ai_model: Optional[str] = None):
        self.use_ai = use_ai
        self.ai_model = ai_model
        self.sections: List[SectionInfo] = []

    def analyze(self, doc: Document) -> Dict:
        """分析文档结构"""
        logger.info("开始结构识别...")

        self.sections = []

        for idx, para in enumerate(doc.paragraphs):
            section_info = self._identify_paragraph(para, idx)
            if section_info:
                self.sections.append(section_info)

        self._refine_sections()
        hierarchy = self._build_hierarchy()
        stats = self._calculate_statistics()
        quality = self._evaluate_quality()

        logger.info(f"结构识别完成: {len(self.sections)} 个章节, 质量评分: {quality:.2f}")

        return {
            "sections": [self._section_to_dict(s) for s in self.sections],
            "hierarchy": hierarchy,
            "stats": stats,
            "quality": quality
        }

    def _identify_paragraph(self, paragraph, index: int) -> Optional[SectionInfo]:
        """识别段落类型，按优先级依次尝试5种策略"""
        text = paragraph.text.strip()
        if not text:
            return None

        # 策略1: 关键词匹配
        result = self._match_keywords(text, index)
        if result and result.confidence >= 0.9:
            return result

        # 策略2: 编号模式匹配
        pattern_result = self._match_patterns(text, index)
        if pattern_result and pattern_result.confidence >= 0.85:
            return pattern_result

        # 策略3: 样式分析
        style_result = self._analyze_style(paragraph, index)
        if style_result and style_result.confidence >= 0.80:
            return style_result

        # 策略4: 格式特征分析
        format_result = self._analyze_format(paragraph, index)
        if format_result and format_result.confidence >= 0.70:
            return format_result

        # 策略5: AI辅助识别（如果启用）
        if self.use_ai:
            ai_result = self._ai_identify(text, index)
            if ai_result:
                return ai_result

        # 返回置信度最高的结果
        best_result = max(
            filter(None, [result, pattern_result, style_result, format_result]),
            key=lambda x: x.confidence,
            default=None
        )
        if best_result:
            return best_result

        # 默认正文
        return SectionInfo(
            index=index,
            type=SectionType.BODY,
            text=text,
            confidence=0.5,
            method="default"
        )

    def _match_keywords(self, text: str, index: int) -> Optional[SectionInfo]:
        """关键词匹配（使用预编译正则）"""
        for section_type, patterns in self.KEYWORDS.items():
            for pattern in patterns:
                if pattern.search(text):
                    return SectionInfo(
                        index=index,
                        type=section_type,
                        text=text,
                        confidence=0.95,
                        method="keyword"
                    )
        return None

    def _match_patterns(self, text: str, index: int) -> Optional[SectionInfo]:
        """编号模式匹配（使用预编译正则）"""
        for section_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = pattern.match(text)
                if match:
                    numbering = match.group(0).strip()
                    level = self._determine_level(section_type, numbering)
                    return SectionInfo(
                        index=index,
                        type=section_type,
                        text=text,
                        level=level,
                        confidence=0.90,
                        method="pattern",
                        numbering=numbering
                    )
        return None

    def _analyze_style(self, paragraph, index: int) -> Optional[SectionInfo]:
        """样式分析"""
        style_name = paragraph.style.name
        if style_name in self.STYLE_MAP:
            section_type = self.STYLE_MAP[style_name]
            level = 0
            if "Heading" in style_name or "标题" in style_name:
                numbers = re.findall(r'\d+', style_name)
                if numbers:
                    level = int(numbers[0])
            return SectionInfo(
                index=index,
                type=section_type,
                text=paragraph.text.strip(),
                level=level,
                confidence=0.85,
                method="style"
            )
        return None

    def _analyze_format(self, paragraph, index: int) -> Optional[SectionInfo]:
        """格式特征分析（字体大小、加粗等）"""
        text = paragraph.text.strip()
        if not paragraph.runs:
            return None

        # 取有效加粗值：优先 run 层显式设置，无则沿样式链查
        explicit_bold = next((r.bold for r in paragraph.runs if r.bold is not None), None)
        if explicit_bold is not None:
            is_bold = explicit_bold
        else:
            is_bold = False
            try:
                style = paragraph.style
                while style is not None:
                    b = style.font.bold
                    if b is not None:
                        is_bold = bool(b)
                        break
                    style = getattr(style, 'base_style', None)
            except Exception:
                pass

        # 取有效字号：优先 run 层显式设置，无则沿样式链查
        font_size = next((r.font.size for r in paragraph.runs if r.font.size is not None), None)
        if font_size is None:
            try:
                style = paragraph.style
                while style is not None:
                    sz = style.font.size
                    if sz is not None:
                        font_size = sz
                        break
                    style = getattr(style, 'base_style', None)
            except Exception:
                pass

        # 检查文本是否以句末标点结尾
        ending_punctuation = r"[。.?？!！]$"
        has_ending_punct = bool(re.search(ending_punctuation, text))

        if font_size:
            size_pt = font_size.pt
            # TITLE：字号 >= 22pt 且加粗，或在文档前3段且字号 >= 16pt 且不以句末标点结尾
            if size_pt >= 22 and is_bold:
                return SectionInfo(index=index, type=SectionType.TITLE,
                                   text=text, level=0, confidence=0.75, method="format")
            elif index <= 2 and size_pt >= 16 and not has_ending_punct:
                return SectionInfo(index=index, type=SectionType.TITLE,
                                   text=text, level=0, confidence=0.70, method="format")
            elif is_bold and size_pt >= 16:
                return SectionInfo(index=index, type=SectionType.CHAPTER,
                                   text=text, level=1, confidence=0.70, method="format")
            elif is_bold and size_pt >= 14:
                return SectionInfo(index=index, type=SectionType.SECTION_1,
                                   text=text, level=2, confidence=0.70, method="format")
        return None

    def _ai_identify(self, text: str, index: int) -> Optional[SectionInfo]:
        """AI 辅助识别章节类型（同步，调用统一 AI 客户端）"""
        try:
            from app.core.proofreadme.llm import llm_fallback

            prompt = """请判断以下文本属于论文的哪个部分。
只返回类型标签，不要任何解释和标点。

可选类型：title, abstract_cn, abstract_en, keywords_cn, keywords_en,
         chapter, section_1, section_2, references, appendix, body

文本：{text}

类型：""".format(text=text[:150])

            response = llm_fallback(prompt).strip().lower()
            response = response.split()[0] if response else ""

            type_map = {
                "title":       SectionType.TITLE,
                "abstract_cn": SectionType.ABSTRACT_CN,
                "abstract_en": SectionType.ABSTRACT_EN,
                "keywords_cn": SectionType.KEYWORDS_CN,
                "keywords_en": SectionType.KEYWORDS_EN,
                "chapter":     SectionType.CHAPTER,
                "section_1":   SectionType.SECTION_1,
                "section_2":   SectionType.SECTION_2,
                "references":  SectionType.REFERENCE,
                "appendix":    SectionType.APPENDIX,
                "body":        SectionType.BODY,
            }

            if response in type_map:
                logger.info(f"[AI识别] index={index} → {response}")
                return SectionInfo(
                    index=index,
                    type=type_map[response],
                    text=text,
                    confidence=0.80,
                    method="ai",
                )
            else:
                logger.warning(f"[AI识别] 返回了未知类型: '{response}'，忽略")

        except Exception as e:
            logger.warning(f"[AI识别] 失败: {e}")

        return None

    def _determine_level(self, section_type: SectionType, numbering: str) -> int:
        """根据章节类型和编号确定层级"""
        if section_type == SectionType.CHAPTER:
            return 1
        elif section_type == SectionType.SECTION_1:
            return 2
        elif section_type == SectionType.SECTION_2:
            return 3
        elif section_type == SectionType.SECTION_3:
            return 4
        dot_count = numbering.count('.')
        return dot_count + 1

    def _build_hierarchy(self) -> Dict:
        """构建层级结构树"""
        hierarchy = {"root": [], "nodes": {}}
        stack = []

        for section in self.sections:
            node = {
                "index": section.index,
                "type": section.type.value,
                "text": section.text,
                "level": section.level,
                "children": []
            }
            while stack and stack[-1]["level"] >= section.level:
                stack.pop()

            if stack:
                parent = stack[-1]
                parent["children"].append(section.index)
                section.parent = parent["index"]
            else:
                hierarchy["root"].append(section.index)

            stack.append(node)
            hierarchy["nodes"][section.index] = node

        return hierarchy

    def _refine_sections(self):
        """优化和修正识别结果"""
        ending_punctuation = r"[。.?？!！]$"

        for section in self.sections:
            if section.type == SectionType.TITLE:
                # 超过 100 字的 TITLE 降为 BODY
                if len(section.text) > 100:
                    section.type = SectionType.BODY
                    section.confidence *= 0.5
                # 在文档第 3 段之后的 TITLE 降为 BODY
                elif section.index > 2 and section.method == "format":
                    section.type = SectionType.BODY
                    section.confidence *= 0.4
                # 以句末标点结尾的 TITLE 降为 BODY
                elif re.search(ending_punctuation, section.text):
                    section.type = SectionType.BODY
                    section.confidence *= 0.3

            if section.type in [SectionType.ABSTRACT_CN, SectionType.ABSTRACT_EN]:
                if len(section.text) < 20:
                    section.confidence *= 0.6

        section_types = {s.type for s in self.sections}
        if SectionType.TITLE not in section_types and self.sections:
            first_section = self.sections[0]
            if first_section.level == 0:
                first_section.type = SectionType.TITLE
                first_section.method = "inferred"

    def _calculate_statistics(self) -> Dict:
        """计算统计信息"""
        stats = {
            "total_sections": len(self.sections),
            "by_type": {},
            "by_method": {},
            "avg_confidence": 0.0,
            "has_abstract": False,
            "has_keywords": False,
            "has_references": False,
            "chapter_count": 0,
            "max_level": 0
        }
        if not self.sections:
            return stats

        for section in self.sections:
            type_name = section.type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
            stats["by_method"][section.method] = stats["by_method"].get(section.method, 0) + 1
            if section.level > stats["max_level"]:
                stats["max_level"] = section.level

        stats["avg_confidence"] = sum(s.confidence for s in self.sections) / len(self.sections)

        types = {s.type for s in self.sections}
        stats["has_abstract"] = (SectionType.ABSTRACT_CN in types or SectionType.ABSTRACT_EN in types)
        stats["has_keywords"] = (SectionType.KEYWORDS_CN in types or SectionType.KEYWORDS_EN in types)
        stats["has_references"] = SectionType.REFERENCE in types
        stats["chapter_count"] = stats["by_type"].get("chapter", 0)

        return stats

    def _evaluate_quality(self) -> float:
        """评估识别质量（置信度40% + 完整性30% + 方法多样性30%）"""
        if not self.sections:
            return 0.0

        avg_confidence = sum(s.confidence for s in self.sections) / len(self.sections)
        confidence_score = avg_confidence * 0.4

        completeness = 0.0
        types = {s.type for s in self.sections}
        if SectionType.TITLE in types:
            completeness += 0.1
        if SectionType.ABSTRACT_CN in types or SectionType.ABSTRACT_EN in types:
            completeness += 0.1
        if SectionType.CHAPTER in types:
            completeness += 0.05
        if SectionType.REFERENCE in types:
            completeness += 0.05
        completeness_score = min(completeness, 0.3)

        methods = [s.method for s in self.sections]
        method_score = (len(set(methods)) / 5) * 0.3

        return min(confidence_score + completeness_score + method_score, 1.0)

    def _section_to_dict(self, section: SectionInfo) -> Dict:
        """转换为字典"""
        return {
            "index": section.index,
            "type": section.type.value,
            "text": section.text,
            "level": section.level,
            "confidence": round(section.confidence, 3),
            "method": section.method,
            "numbering": section.numbering,
            "parent": section.parent
        }

    def export_outline(self) -> str:
        """导出大纲（Markdown格式）"""
        lines = ["# 论文大纲\n"]
        for section in self.sections:
            if section.type in [SectionType.BODY, SectionType.UNKNOWN]:
                continue
            indent = "  " * (section.level - 1) if section.level > 0 else ""
            lines.append(f"{indent}- {section.text}")
        return "\n".join(lines)
