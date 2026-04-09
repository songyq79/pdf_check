"""
论文格式化模块
"""

from app.core.formatter.format_engine import FormatEngine
from app.core.formatter.template_manager import TemplateManager
from app.core.formatter.structure_analyzer import StructureAnalyzer
from app.core.formatter.style_applicator import StyleApplicator

__all__ = ["FormatEngine", "TemplateManager", "StructureAnalyzer", "StyleApplicator"]
__version__ = "2.0.0"