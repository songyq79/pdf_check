# backend/app/core/formatter/format_engine.py
"""
格式化引擎 - 整合所有组件
"""

from docx import Document
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from datetime import datetime
import zipfile
import xml.etree.ElementTree as ET

from .template_manager import TemplateManager
from .structure_analyzer import StructureAnalyzer
from .style_applicator import StyleApplicator


class FormatEngine:
    """
    企业级格式化引擎
    
    整合所有格式化组件，提供统一接口
    """
    
    def __init__(self, template_dir: Path, use_ai: bool = False):
        self.template_manager = TemplateManager(
            builtin_dir=template_dir / "builtin",
            user_dir=template_dir / "user"
        )
        
        self.analyzer = StructureAnalyzer(use_ai=use_ai)
        
        logger.info(f"格式化引擎初始化完成 (AI: {use_ai})")
    
    def _extract_text_fallback(self, input_path: str) -> str:
        """
        降级方案：从损坏的文档中提取纯文本
        
        尝试多种方法提取文本内容：
        1. 直接解析 ZIP 中的 document.xml
        2. 使用 zipfile 提取所有文本节点
        """
        try:
            # 方法1：解析 document.xml
            with zipfile.ZipFile(input_path, 'r') as docx_zip:
                # 读取主文档 XML
                xml_content = docx_zip.read('word/document.xml')
                root = ET.fromstring(xml_content)
                
                # 提取所有文本节点
                namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                text_elements = root.findall('.//w:t', namespace)
                
                text_content = '\n'.join([elem.text for elem in text_elements if elem.text])
                
                if text_content.strip():
                    logger.info(f"  降级提取成功: {len(text_content)} 字符")
                    return text_content
                
        except Exception as e:
            logger.warning(f"  降级提取失败: {e}")
        
        return ""
    
    def _create_simple_document(self, text_content: str, template_id: str, output_path: str) -> Dict:
        """
        降级方案：创建简化的格式化文档
        
        只保留文本内容，应用基本的模板样式
        """
        try:
            # 创建新文档
            doc = Document()
            
            # 加载模板配置
            template_config = self.template_manager.extract_config(template_id)
            template_meta = self.template_manager.get_template(template_id)
            
            # 按段落分割文本
            paragraphs = [p.strip() for p in text_content.split('\n') if p.strip()]
            
            # 添加段落到文档
            for para_text in paragraphs:
                doc.add_paragraph(para_text)
            
            # 应用基本样式（如果模板支持）
            try:
                applicator = StyleApplicator(template_config)
                # 简化的章节结构（所有段落都当作正文）
                simple_sections = [{'type': 'body', 'start': 0, 'end': len(paragraphs)}]
                doc = applicator.apply(doc, simple_sections)
            except Exception as e:
                logger.warning(f"  样式应用失败（使用默认样式）: {e}")
            
            # 保存文档
            doc.save(output_path)
            
            logger.info(f"  简化文档生成成功: {len(paragraphs)} 个段落")
            
            return {
                'success': True,
                'fallback_mode': True,
                'paragraphs': len(paragraphs),
                'template': {
                    'id': template_id,
                    'name': template_meta.name
                }
            }
            
        except Exception as e:
            logger.error(f"  简化文档生成失败: {e}")
            raise
    
    def format_document(
        self,
        input_path: str,
        output_path: str,
        template_id: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        格式化文档（主入口）
        
        Args:
            input_path: 输入文档路径
            output_path: 输出文档路径
            template_id: 模板ID
            options: 可选配置
        
        Returns:
            格式化结果
        """
        start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info(f"开始格式化")
        logger.info(f"输入: {input_path}")
        logger.info(f"模板: {template_id}")
        logger.info("=" * 60)
        
        try:
            # 1. 加载文档
            logger.info("[1/5] 加载文档...")
            doc = Document(input_path)
            para_count = len(doc.paragraphs)
            logger.info(f"  文档加载成功: {para_count} 个段落")
            
            # 2. 识别结构
            logger.info("[2/5] 识别结构...")
            analysis_result = self.analyzer.analyze(doc)
            
            logger.info(
                f"  识别完成: {len(analysis_result['sections'])} 个章节, "
                f"质量: {analysis_result['quality']:.2%}"
            )
            
            # 3. 加载模板
            logger.info("[3/5] 加载模板...")
            template_config = self.template_manager.extract_config(template_id)
            template_meta = self.template_manager.get_template(template_id)
            
            logger.info(f"  模板: {template_meta.name}")
            
            # 4. 应用样式
            logger.info("[4/5] 应用样式...")
            applicator = StyleApplicator(template_config)
            doc = applicator.apply(doc, analysis_result['sections'])
            
            logger.info(
                f"  应用完成: 成功 {applicator.applied_count}, "
                f"失败 {applicator.error_count}"
            )
            
            # 5. 保存文档
            logger.info("[5/5] 保存文档...")
            doc.save(output_path)
            
            # 计算耗时
            time_elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info(f"✅ 格式化完成！耗时: {time_elapsed:.2f}秒")
            logger.info(f"输出: {output_path}")
            logger.info("=" * 60)
            
            return {
                'success': True,
                'structure': analysis_result,
                'template': {
                    'id': template_id,
                    'name': template_meta.name
                },
                'stats': {
                    'paragraphs': para_count,
                    'sections': len(analysis_result['sections']),
                    'applied': applicator.applied_count,
                    'errors': applicator.error_count,
                    'quality': analysis_result['quality']
                },
                'time_elapsed': time_elapsed,
                'output_path': output_path
            }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 格式化失败: {error_msg}")
            
            # 判断是否是文档格式问题
            if "no item named" in error_msg.lower() or "badzip" in error_msg.lower():
                logger.warning("⚠️ 检测到文档格式异常，尝试降级处理...")
                
                try:
                    # 尝试降级处理：提取文本 + 简化格式化
                    text_content = self._extract_text_fallback(input_path)
                    
                    if text_content:
                        result = self._create_simple_document(text_content, template_id, output_path)
                        time_elapsed = (datetime.now() - start_time).total_seconds()
                        
                        logger.warning("=" * 60)
                        logger.warning(f"⚠️ 降级处理完成！耗时: {time_elapsed:.2f}秒")
                        logger.warning(f"输出: {output_path}")
                        logger.warning("=" * 60)
                        
                        return {
                            'success': True,
                            'warning': '文档格式异常，已使用简化模式处理（可能丢失部分格式、图片等内容）',
                            'fallback_mode': True,
                            'stats': {
                                'paragraphs': result.get('paragraphs', 0),
                                'sections': 0,
                                'applied': 0,
                                'errors': 0,
                                'quality': 0.0
                            },
                            'template': result.get('template', {}),
                            'time_elapsed': time_elapsed,
                            'output_path': output_path
                        }
                    else:
                        # 文本提取也失败
                        logger.error("❌ 降级处理失败：无法提取文本内容")
                        
                except Exception as fallback_error:
                    logger.error(f"❌ 降级处理失败: {fallback_error}")
                
                # 降级处理失败，返回友好错误
                return {
                    'success': False,
                    'error': '文档格式异常且无法自动修复',
                    'detail': '文档内部结构损坏或格式不正确',
                    'suggestions': [
                        '请在 Word 中打开文档，选择"另存为"，保存为新的 .docx 文件',
                        '确保文档能在 Word 中正常打开',
                        '尝试删除文档中的特殊对象（如嵌入的 OLE 对象、损坏的图片等）'
                    ],
                    'time_elapsed': (datetime.now() - start_time).total_seconds()
                }
            
            # 其他类型的错误，直接返回
            return {
                'success': False,
                'error': error_msg,
                'time_elapsed': (datetime.now() - start_time).total_seconds()
            }
    
    def preview_structure(self, input_path: str) -> Dict:
        """预览文档结构（不格式化）"""
        doc = Document(input_path)
        return self.analyzer.analyze(doc)
    
    def validate_template(self, template_file: str) -> Dict:
        """验证模板文件"""
        return self.template_manager.validate_template(template_file)
    
    def get_template_list(self, category: str = None) -> list:
        """获取模板列表"""
        return [
            {
                'id': t.template_id,
                'name': t.name,
                'category': t.category,
                'school': t.school_or_journal,
                'usage_count': t.usage_count
            }
            for t in self.template_manager.list_templates(category=category)
        ]
