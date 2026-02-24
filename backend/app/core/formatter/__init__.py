"""
论文格式化模块
提供企业级的论文格式化功能
"""

from .format_engine import FormatEngine
from .template_manager import TemplateManager
from .structure_analyzer import StructureAnalyzer
from.style_applicator import StyleApplicator

__all__ = [
    'FormatEngine',
    'TemplateManager',
    'StructureAnalyzer',
    'StyleApplicator'
]

__version__ = '1.0.0'