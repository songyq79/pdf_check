# backend/app/core/formatter/template_manager.py
"""
企业级模板管理器
支持模板CRUD、缓存、版本控制
"""


from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import hashlib
import shutil  #文件复制、移动操作
from loguru import logger

from docx import Document
from docx.shared import Pt, Inches, RGBColor  #Word 字体尺寸、颜色单位。
from docx.enum.text import WD_ALIGN_PARAGRAPH  #Word 对齐方式枚举。
from docx.oxml.ns import qn  #XML 命名空间工具（高级 Word 操作）


@dataclass
class TemplateMetadata:   #定义模板数据库模型（类似 ORM 表结构）。
    """模板元数据"""
    template_id: str  #模板唯一ID
    name: str
    category: str  # 分类：大学模板、期刊模板、自定义模板
    school_or_journal: str  #学校名或期刊名。
    description: str
    version: str = "1.0"
    author: str = "system"
    created_at: str = None
    updated_at: str = None
    usage_count: int = 0   #使用次数统计（推荐排序用）。
    is_public: bool = True  #是否内置模板（不可删除）。
    tags: List[str] = None  #模板标签（搜索用）
    file_path: str = None  #Word 文件路径、
    preview_image: str = None  #预览图路径
    
    def __post_init__(self):  #__post_init__ = dataclass 构造函数之后自动执行的钩子函数
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []


@dataclass
class TemplateConfig:
    """模板配置结构"""
    
    # 页面设置
    page_width: float  # 单位：cm
    page_height: float
    margin_top: float   #页边距。
    margin_bottom: float
    margin_left: float
    margin_right: float
    
    # 样式配置
    styles: Dict[str, Dict]  # 样式名 -> 样式配置Word 样式库提取结果。
    
    # 编号配置
    numbering: Dict[str, str]  # 章节编号类型 -> 格式
    
    # 页眉页脚
    header: Optional[Dict] = None
    footer: Optional[Dict] = None
    
    # 其他配置
    line_number: bool = False
    track_changes: bool = False


class TemplateManager:
    """
    企业级模板管理器
    
    功能:
    - 模板CRUD操作
    - 样式提取和应用
    - 模板缓存机制
    - 版本控制
    - 模板验证
    """
    
    def __init__(
        self, 
        builtin_dir: Path,
        user_dir: Path,
        cache_dir: Optional[Path] = None
    ):   #三种模板目录
        self.builtin_dir = Path(builtin_dir)
        self.user_dir = Path(user_dir)
        self.cache_dir = Path(cache_dir) if cache_dir else self.user_dir / ".cache"
        
        # 创建必要目录
        self.builtin_dir.mkdir(parents=True, exist_ok=True)  #自动创建目录（Linux/Windows 兼容
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 模板索引（内存缓存）
        self._template_index: Dict[str, TemplateMetadata] = {}
        self._config_cache: Dict[str, TemplateConfig] = {}
        
        # 初始化索引
        self._build_index()
        
        logger.info(f"模板管理器初始化完成")
        logger.info(f"内置模板目录: {self.builtin_dir}")
        logger.info(f"用户模板目录: {self.user_dir}")
    
    def _build_index(self):
        """构建模板索引"""
        # 扫描内置模板
        self._scan_directory(self.builtin_dir, is_builtin=True)
        
        # 扫描用户模板
        self._scan_directory(self.user_dir, is_builtin=False)
        
        logger.info(f"索引构建完成，共 {len(self._template_index)} 个模板")
    
    def _scan_directory(self, directory: Path, is_builtin: bool):
        """扫描目录中的模板"""
        if not directory.exists():
            return
        
        for template_file in directory.rglob("*.docx"): #递归遍历目录下所有 .docx 文件（包括子目录）返回的是 Path 对象，不是字符串
            # 跳过临时文件
            if template_file.name.startswith("~"):#过滤临时文件
                continue
            
            try:
                # 读取元数据
                metadata_file = template_file.with_suffix(".json") #把文件扩展名改为 .json，返回新的Path
                
                if metadata_file.exists():
                    # 从JSON读取
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata_dict = json.load(f) #从文件对象 f 中读取 JSON 内容，并解析成 Python 字典（dict）
                        metadata = TemplateMetadata(**metadata_dict)
                else:
                    # 自动生成元数据
                    metadata = self._generate_metadata(template_file, is_builtin)
                
                metadata.file_path = str(template_file)
                self._template_index[metadata.template_id] = metadata
                
                logger.debug(f"索引模板: {metadata.name}")
            
            except Exception as e:
                logger.error(f"索引模板失败 {template_file}: {e}")
    
    def _generate_metadata(self, template_file: Path, is_builtin: bool) -> TemplateMetadata:
        """自动生成模板元数据"""
        # 从文件名提取信息
        name = template_file.stem
        
        # 生成template_id
        template_id = hashlib.md5(
            str(template_file).encode()
        ).hexdigest()[:16]
        
        # 判断分类
        category = "builtin" if is_builtin else "custom"
        if "university" in str(template_file).lower() or "大学" in name:
            category = "universities"
        elif "journal" in str(template_file).lower() or "期刊" in name:
            category = "journals"
        
        return TemplateMetadata(
            template_id=template_id,
            name=name,
            category=category,
            school_or_journal=name,
            description=f"自动生成的模板：{name}",
            is_public=is_builtin
        )
    
    def get_template(self, template_id: str) -> Optional[TemplateMetadata]:
        """获取模板元数据"""
        return self._template_index.get(template_id)
    
    def list_templates(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[TemplateMetadata]:
        """
        列出模板
        
        Args:
            category: 分类过滤
            search: 搜索关键词
            limit: 返回数量限制
        """
        templates = list(self._template_index.values())
        
        # 分类过滤
        if category:
            templates = [t for t in templates if t.category == category]
        
        # 搜索过滤
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.name.lower() or
                   search_lower in t.school_or_journal.lower() or
                   search_lower in t.description.lower()
            ]
        
        # 排序（按使用次数降序）
        templates.sort(key=lambda x: x.usage_count, reverse=True)
        
        return templates[:limit]
    
    def load_document(self, template_id: str) -> Document:
        """加载模板文档"""
        metadata = self.get_template(template_id)

        if not metadata:
            raise ValueError(f"模板不存在: {template_id}")

        try:
            doc = Document(metadata.file_path)

            # 更新使用次数（后台线程写磁盘，不阻塞格式化主流程）
            metadata.usage_count += 1
            import threading
            threading.Thread(
                target=self._save_metadata,
                args=(metadata,),
                daemon=True
            ).start()

            logger.info(f"模板已加载: {metadata.name}")
            return doc

        except Exception as e:
            logger.error(f"加载模板失败: {e}")
            raise
    
    def extract_config(self, template_id: str) -> TemplateConfig:
        """
        提取模板配置
        带缓存机制
        """
        # 检查缓存
        if template_id in self._config_cache:
            logger.debug(f"从缓存读取配置: {template_id}")
            return self._config_cache[template_id]
        
        # 加载文档
        doc = self.load_document(template_id)
        
        # 提取配置
        config = TemplateConfig(
            page_width=self._extract_page_width(doc),
            page_height=self._extract_page_height(doc),
            margin_top=self._extract_margin(doc, 'top'),
            margin_bottom=self._extract_margin(doc, 'bottom'),
            margin_left=self._extract_margin(doc, 'left'),
            margin_right=self._extract_margin(doc, 'right'),
            styles=self._extract_styles(doc),
            numbering=self._extract_numbering(doc),
            header=self._extract_header(doc),
            footer=self._extract_footer(doc)
        )
        
        # 缓存配置
        self._config_cache[template_id] = config
        
        logger.info(f"配置提取完成: {template_id}")
        return config
    
    def _extract_page_width(self, doc: Document) -> float:
        """提取页面宽度（cm）"""
        section = doc.sections[0]
        return section.page_width.cm
    
    def _extract_page_height(self, doc: Document) -> float:
        """提取页面高度（cm）"""
        section = doc.sections[0]
        return section.page_height.cm
    
    def _extract_margin(self, doc: Document, position: str) -> float:
        """提取页边距（cm）"""
        section = doc.sections[0]
        margin_map = {
            'top': section.top_margin,
            'bottom': section.bottom_margin,
            'left': section.left_margin,
            'right': section.right_margin
        }
        return margin_map[position].cm
    
    def _extract_styles(self, doc: Document) -> Dict[str, Dict]:
        """提取段落样式"""
        styles = {}
        
        for style in doc.styles:
            # 只提取段落样式
            if style.type != 1:  # 1 = WD_STYLE_TYPE.PARAGRAPH
                continue
            
            try:
                style_config = {
                    "name": style.name,
                    "font_name": None,
                    "font_size": None,
                    "bold": False,
                    "italic": False,
                    "underline": False,
                    "color": None,
                    "alignment": None,
                    "line_spacing": None,
                    "space_before": None,
                    "space_after": None,
                    "first_line_indent": None,
                    "left_indent": None,
                    "right_indent": None
                }
                
                # 字体属性
                if style.font.name:
                    style_config["font_name"] = style.font.name
                if style.font.size:
                    style_config["font_size"] = style.font.size.pt
                style_config["bold"] = style.font.bold or False
                style_config["italic"] = style.font.italic or False
                style_config["underline"] = style.font.underline or False
                
                # 段落格式
                pf = style.paragraph_format
                if pf.alignment:
                    style_config["alignment"] = str(pf.alignment)
                if pf.line_spacing:
                    style_config["line_spacing"] = pf.line_spacing
                if pf.space_before:
                    style_config["space_before"] = pf.space_before.pt
                if pf.space_after:
                    style_config["space_after"] = pf.space_after.pt
                if pf.first_line_indent:
                    style_config["first_line_indent"] = pf.first_line_indent.cm
                if pf.left_indent:
                    style_config["left_indent"] = pf.left_indent.cm
                if pf.right_indent:
                    style_config["right_indent"] = pf.right_indent.cm
                
                styles[style.name] = style_config
            
            except Exception as e:
                logger.warning(f"提取样式失败 {style.name}: {e}")
        
        return styles
    
    def _extract_numbering(self, doc: Document) -> Dict[str, str]:
        """提取编号配置"""
        # 这里可以实现更复杂的编号提取逻辑
        # 默认返回标准编号格式
        return {
            "chapter": "第{n}章",
            "section1": "{n}",
            "section2": "{n}.{m}",
            "section3": "{n}.{m}.{k}"
        }
    
    def _extract_header(self, doc: Document) -> Optional[Dict]:
        """提取页眉配置"""
        try:
            section = doc.sections[0]
            if section.header:
                return {
                    "text": section.header.paragraphs[0].text if section.header.paragraphs else "",
                    "align": "center"
                }
        except:
            pass
        return None
    
    def _extract_footer(self, doc: Document) -> Optional[Dict]:
        """提取页脚配置"""
        try:
            section = doc.sections[0]
            if section.footer:
                return {
                    "text": section.footer.paragraphs[0].text if section.footer.paragraphs else "",
                    "align": "center",
                    "page_number": True
                }
        except:
            pass
        return None
    
    def save_template(
        self,
        file_path: Union[str, Path],
        metadata: TemplateMetadata
    ) -> str:
        """
        保存用户上传的模板
        
        Returns:
            template_id
        """
        file_path = Path(file_path)
        
        # 生成保存路径
        save_dir = self.user_dir / metadata.category
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        template_file = save_dir / f"{metadata.template_id}.docx"
        shutil.copy(file_path, template_file)
        
        # 更新元数据
        metadata.file_path = str(template_file)
        metadata.created_at = datetime.now().isoformat()
        
        # 保存元数据
        self._save_metadata(metadata)
        
        # 更新索引
        self._template_index[metadata.template_id] = metadata
        
        logger.info(f"模板已保存: {metadata.name}")
        
        return metadata.template_id
    
    def _save_metadata(self, metadata: TemplateMetadata):
        """保存元数据到JSON文件"""
        if not metadata.file_path:
            return
        
        metadata_file = Path(metadata.file_path).with_suffix(".json")
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        metadata = self.get_template(template_id)
        
        if not metadata:
            return False
        
        # 只能删除用户模板
        if metadata.is_public:
            raise PermissionError("不能删除内置模板")
        
        try:
            # 删除文件
            Path(metadata.file_path).unlink()
            
            # 删除元数据文件
            metadata_file = Path(metadata.file_path).with_suffix(".json")
            if metadata_file.exists():
                metadata_file.unlink()
            
            # 从索引移除
            del self._template_index[template_id]
            
            # 清除缓存
            if template_id in self._config_cache:
                del self._config_cache[template_id]
            
            logger.info(f"模板已删除: {metadata.name}")
            return True
        
        except Exception as e:
            logger.error(f"删除模板失败: {e}")
            return False
    
    def validate_template(self, file_path: Union[str, Path]) -> Dict:
        """
        验证模板文件
        
        Returns:
            验证结果 {valid: bool, errors: List[str], warnings: List[str]}
        """
        errors = []
        warnings = []
        
        try:
            doc = Document(file_path)
            
            # 检查是否有样式
            if len(doc.styles) == 0:
                warnings.append("模板中没有自定义样式")
            
            # 检查是否有内容
            if len(doc.paragraphs) == 0:
                warnings.append("模板中没有示例内容")
            
            # 检查页面设置
            section = doc.sections[0]
            if section.page_width.cm < 10 or section.page_height.cm < 10:
                errors.append("页面尺寸异常")
            
        except Exception as e:
            errors.append(f"无法打开文件: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        templates = list(self._template_index.values())
        
        return {
            "total": len(templates),
            "categories": {
                "universities": len([t for t in templates if t.category == "universities"]),
                "journals": len([t for t in templates if t.category == "journals"]),
                "custom": len([t for t in templates if t.category == "custom"])
            },
            "most_used": sorted(templates, key=lambda x: x.usage_count, reverse=True)[:5],
            "cache_size": len(self._config_cache)
        }
