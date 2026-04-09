# backend/app/core/formatter/style_applicator.py
"""
企业级样式应用器
支持复杂的样式映射和批量应用
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from typing import Dict, List
from loguru import logger

from .structure_analyzer import SectionInfo, SectionType
from .template_manager import TemplateConfig


class StyleApplicator:
    """
    样式应用器
    
    功能：
    - 页面设置应用
    - 字体样式应用  
    - 段落格式应用
    - 编号应用
    - 页眉页脚应用
    """
    
    def __init__(self, config: TemplateConfig):
        self.config = config
        self.applied_count = 0
        self.error_count = 0
    
    def apply(self, doc: Document, sections: List[Dict]) -> Document:
        """
        应用样式到文档
        
        Args:
            doc: Word文档对象
            sections: 识别的章节列表
        """
        logger.info("开始应用样式...")
        
        # 1. 页面设置
        self._apply_page_setup(doc)
        
        # 2. 批量应用段落样式
        for section in sections:
            try:
                para = doc.paragraphs[section['index']]
                self._apply_paragraph_style(para, section)
                self.applied_count += 1
            except Exception as e:
                logger.error(f"应用样式失败 [{section['index']}]: {e}")
                self.error_count += 1
        
        # 3. 应用编号
        self._apply_numbering(doc, sections)
        
        # 4. 页眉页脚
        if self.config.header or self.config.footer:
            self._apply_header_footer(doc)
        
        logger.info(f"样式应用完成: 成功 {self.applied_count}, 失败 {self.error_count}")
        
        return doc
    
    def _apply_page_setup(self, doc: Document):
        """应用页面设置"""
        section = doc.sections[0]
        
        # 页面尺寸
        section.page_width = Cm(self.config.page_width)
        section.page_height = Cm(self.config.page_height)
        
        # 页边距
        section.top_margin = Cm(self.config.margin_top)
        section.bottom_margin = Cm(self.config.margin_bottom)
        section.left_margin = Cm(self.config.margin_left)
        section.right_margin = Cm(self.config.margin_right)
        
        logger.info(
            f"页面设置: {self.config.page_width}×{self.config.page_height}cm, "
            f"边距: T{self.config.margin_top}/B{self.config.margin_bottom}/"
            f"L{self.config.margin_left}/R{self.config.margin_right}cm"
        )
    
    def _apply_paragraph_style(self, paragraph, section: Dict):
        """应用段落样式"""
        section_type = section['type']
        
        # 样式映射
        style_map = {
            'title': 'title',
            'chapter': 'heading1',
            'section_1': 'heading2',
            'section_2': 'heading3',
            'section_3': 'heading4',
            'abstract_cn': 'abstract',
            'abstract_en': 'abstract',
            'body': 'body',
            'references': 'references'
        }
        
        style_name = style_map.get(section_type, 'body')
        style_config = self.config.styles.get(style_name, {})
        
        if not style_config:
            return
        
        # 应用字体
        self._apply_font(paragraph, style_config)
        
        # 应用段落格式
        self._apply_format(paragraph, style_config)
    
    def _apply_font(self, paragraph, config: Dict):
        """应用字体样式"""
        for run in paragraph.runs:
            if config.get('font_name'):
                run.font.name = config['font_name']
                run._element.rPr.rFonts.set(qn('w:eastAsia'), config['font_name'])
            
            if config.get('font_size'):
                run.font.size = Pt(config['font_size'])
            
            if config.get('bold'):
                run.font.bold = True
            
            if config.get('italic'):
                run.font.italic = True
    
    def _apply_format(self, paragraph, config: Dict):
        """应用段落格式"""
        pf = paragraph.paragraph_format
        
        # 对齐
        if config.get('alignment'):
            align_map = {
                'left': WD_ALIGN_PARAGRAPH.LEFT,
                'center': WD_ALIGN_PARAGRAPH.CENTER,
                'right': WD_ALIGN_PARAGRAPH.RIGHT,
                'justify': WD_ALIGN_PARAGRAPH.JUSTIFY
            }
            pf.alignment = align_map.get(config['alignment'], WD_ALIGN_PARAGRAPH.LEFT)
        
        # 行距
        if config.get('line_spacing'):
            pf.line_spacing = config['line_spacing']
        
        # 段前段后
        if config.get('space_before'):
            pf.space_before = Pt(config['space_before'])
        if config.get('space_after'):
            pf.space_after = Pt(config['space_after'])
        
        # 缩进
        if config.get('first_line_indent'):
            pf.first_line_indent = Cm(config['first_line_indent'])
        if config.get('left_indent'):
            pf.left_indent = Cm(config['left_indent'])
    
    def _apply_numbering(self, doc: Document, sections: List[Dict]):
        """应用编号"""
        logger.info("应用编号...")
        
        chapter_num = 0
        section_nums = {}
        
        for section in sections:
            stype = section['type']
            para = doc.paragraphs[section['index']]
            
            if stype == 'chapter':
                chapter_num += 1
                section_nums = {1: chapter_num, 2: 0, 3: 0}
                
                if not section.get('numbering'):
                    fmt = self.config.numbering.get('chapter', '第{n}章')
                    para.text = f"{fmt.format(n=chapter_num)} {para.text}"
            
            elif stype == 'section_1':
                section_nums[2] = section_nums.get(2, 0) + 1
                section_nums[3] = 0
                
                if not section.get('numbering'):
                    fmt = self.config.numbering.get('section1', '{n}')
                    para.text = f"{fmt.format(n=section_nums[2])} {para.text}"
            
            elif stype == 'section_2':
                section_nums[3] = section_nums.get(3, 0) + 1
                
                if not section.get('numbering'):
                    fmt = self.config.numbering.get('section2', '{n}.{m}')
                    para.text = f"{fmt.format(n=section_nums[2], m=section_nums[3])} {para.text}"
    
    def _apply_header_footer(self, doc: Document):
        """应用页眉页脚"""
        section = doc.sections[0]
        
        # 页眉
        if self.config.header:
            header = section.header
            para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            para.text = self.config.header.get('text', '')
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 页脚  
        if self.config.footer:
            footer = section.footer
            para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            
            if self.config.footer.get('page_number'):
                self._add_page_number(para)
            else:
                para.text = self.config.footer.get('text', '')
            
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    def _add_page_number(self, paragraph):
        """添加页码"""
        run = paragraph.add_run()
        
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = "PAGE"
        
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        
        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)
