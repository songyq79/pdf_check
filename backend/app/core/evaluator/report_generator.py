"""
评价报告生成器 - 生成Word格式的评价报告
使用python-docx库生成格式良好的评价报告
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import logging

from app.schemas.evaluation import EvaluationResponse, EvaluationResult
from app.core.evaluator.chart_generator import generate_radar_chart

logger = logging.getLogger(__name__)


class ReportGenerator:
    """评价报告生成器"""

    def __init__(self):
        """初始化报告生成器"""
        pass

    def generate_report(
        self,
        evaluation: EvaluationResponse,
        output_path: Path,
        include_chart: bool = True
    ) -> Path:
        """
        生成评价报告

        :param evaluation: 评价结果数据
        :param output_path: 输出文件路径
        :param include_chart: 是否包含雷达图
        :return: 生成的报告文件路径
        """
        try:
            # 创建文档
            doc = Document()

            # 设置文档默认字体
            self._set_document_style(doc)

            # 添加标题
            self._add_title(doc, "论文智能评价报告")

            # 添加基本信息
            self._add_basic_info(doc, evaluation)

            # 添加综合评分
            self._add_overall_score(doc, evaluation.overall_score)

            # 添加雷达图（如果需要）
            if include_chart:
                chart_path = self._generate_and_add_chart(doc, evaluation, output_path)

            # 添加分维度评价
            self._add_dimension_evaluations(doc, evaluation)

            # 添加页脚
            self._add_footer(doc)

            # 保存文档
            output_path.parent.mkdir(parents=True, exist_ok=True)
            doc.save(output_path)

            logger.info(f"评价报告生成成功: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"报告生成失败: {str(e)}")
            raise ReportGenerationError(f"报告生成失败: {str(e)}")

    def _set_document_style(self, doc: Document):
        """设置文档样式"""
        # 设置中文字体
        doc.styles['Normal'].font.name = 'SimSun'
        doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
        doc.styles['Normal'].font.size = Pt(10.5)

    def _add_title(self, doc: Document, title: str):
        """添加文档标题"""
        title_para = doc.add_paragraph()
        title_run = title_para.add_run(title)
        title_run.font.size = Pt(22)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(0, 51, 102)
        title_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # 添加空行
        doc.add_paragraph()

    def _add_basic_info(self, doc: Document, evaluation: EvaluationResponse):
        """添加基本信息"""
        # 论文标题
        p = doc.add_paragraph()
        p.add_run("论文标题：").font.bold = True
        p.add_run(evaluation.paper_title)

        # 评价时间
        p = doc.add_paragraph()
        p.add_run("评价时间：").font.bold = True
        p.add_run(evaluation.evaluated_at.strftime("%Y年%m月%d日 %H:%M:%S"))

        # 添加分隔线
        doc.add_paragraph("_" * 80)

    def _add_overall_score(self, doc: Document, score: float):
        """添加综合评分"""
        doc.add_heading("一、综合评分", level=1)

        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        score_run = p.add_run(f"{score:.1f}")
        score_run.font.size = Pt(48)
        score_run.font.bold = True
        score_run.font.color.rgb = self._get_score_color(score)

        p.add_run(" / 100").font.size = Pt(16)

        # 评分等级
        grade = self._get_score_grade(score)
        grade_p = doc.add_paragraph()
        grade_p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        grade_run = grade_p.add_run(f"评价等级：{grade}")
        grade_run.font.size = Pt(14)
        grade_run.font.bold = True

        doc.add_paragraph()

    def _generate_and_add_chart(
        self,
        doc: Document,
        evaluation: EvaluationResponse,
        output_path: Path
    ) -> Optional[Path]:
        """生成并添加雷达图"""
        try:
            # 准备雷达图数据
            dimensions_data = {
                result.dimension_name: result.score
                for result in evaluation.dimensions.values()
            }

            # 生成雷达图
            chart_filename = output_path.stem + "_radar.png"
            chart_path = output_path.parent / chart_filename

            generate_radar_chart(
                dimensions=dimensions_data,
                output_path=chart_path,
                title=f"《{evaluation.paper_title}》评价雷达图"
            )

            # 添加图表标题
            doc.add_heading("二、评价维度分析", level=1)

            # 插入图片
            doc.add_picture(str(chart_path), width=Inches(5.5))
            last_paragraph = doc.paragraphs[-1]
            last_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            doc.add_paragraph()

            return chart_path

        except Exception as e:
            logger.warning(f"雷达图生成失败，跳过图表: {str(e)}")
            return None

    def _add_dimension_evaluations(self, doc: Document, evaluation: EvaluationResponse):
        """添加各维度详细评价"""
        doc.add_heading("三、分维度评价", level=1)

        # 维度顺序
        dimension_order = [
            "academic_standard",
            "logic_innovation",
            "language_quality",
            "citation_standard"
        ]

        for idx, dimension_key in enumerate(dimension_order, 1):
            if dimension_key not in evaluation.dimensions:
                continue

            result = evaluation.dimensions[dimension_key]

            # 维度标题
            heading = f"{idx}. {result.dimension_name}"
            doc.add_heading(heading, level=2)

            # 得分
            score_p = doc.add_paragraph()
            score_p.add_run("得分：").font.bold = True
            score_run = score_p.add_run(f"{result.score}")
            score_run.font.bold = True
            score_run.font.size = Pt(14)
            score_run.font.color.rgb = self._get_score_color(result.score)
            score_p.add_run(" / 100")

            # 优点
            if result.strengths:
                p = doc.add_paragraph()
                p.add_run("优点：").font.bold = True

                for strength in result.strengths:
                    doc.add_paragraph(strength, style='List Bullet')

            # 不足
            if result.weaknesses:
                p = doc.add_paragraph()
                p.add_run("不足之处：").font.bold = True

                for weakness in result.weaknesses:
                    doc.add_paragraph(weakness, style='List Bullet')

            # 改进建议
            if result.suggestions:
                p = doc.add_paragraph()
                p.add_run("改进建议：").font.bold = True

                for suggestion in result.suggestions:
                    doc.add_paragraph(suggestion, style='List Bullet')

            # 添加分隔线（最后一个维度除外）
            if idx < len(dimension_order):
                doc.add_paragraph()

    def _add_footer(self, doc: Document):
        """添加页脚"""
        doc.add_paragraph()
        doc.add_paragraph("_" * 80)

        footer_p = doc.add_paragraph()
        footer_p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        footer_run = footer_p.add_run("本报告由论文智能评价系统自动生成")
        footer_run.font.size = Pt(9)
        footer_run.font.color.rgb = RGBColor(128, 128, 128)
        footer_run.italic = True

    def _get_score_color(self, score: float) -> RGBColor:
        """根据分数获取颜色"""
        if score >= 90:
            return RGBColor(0, 128, 0)  # 绿色 - 优秀
        elif score >= 80:
            return RGBColor(0, 100, 200)  # 蓝色 - 良好
        elif score >= 70:
            return RGBColor(255, 165, 0)  # 橙色 - 中等
        elif score >= 60:
            return RGBColor(255, 140, 0)  # 深橙色 - 及格
        else:
            return RGBColor(255, 0, 0)  # 红色 - 不及格

    def _get_score_grade(self, score: float) -> str:
        """根据分数获取等级"""
        if score >= 90:
            return "优秀 (A)"
        elif score >= 80:
            return "良好 (B)"
        elif score >= 70:
            return "中等 (C)"
        elif score >= 60:
            return "及格 (D)"
        else:
            return "不及格 (F)"


class ReportGenerationError(Exception):
    """报告生成错误"""
    pass


# 工厂函数
def generate_report(
    evaluation: EvaluationResponse,
    output_path: Path,
    include_chart: bool = True
) -> Path:
    """
    生成评价报告的便捷函数

    :param evaluation: 评价结果
    :param output_path: 输出路径
    :param include_chart: 是否包含图表
    :return: 报告文件路径
    """
    generator = ReportGenerator()
    return generator.generate_report(evaluation, output_path, include_chart)