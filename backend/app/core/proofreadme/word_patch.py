"""
Word 修订节点生成工具

生成符合 OOXML 规范的 w:del / w:ins 修订节点，
用于在 Word 中实现 Track Changes（修订模式）。

关键原则：
- 每个修订节点必须有唯一的 w:id（正整数）
- w:del 内用 w:delText，w:ins 内用 w:t
- 需要保留原始 run 的字体/样式属性（w:rPr）
"""

import uuid
from copy import deepcopy
from datetime import datetime, timezone
from lxml import etree

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

AUTHOR = "AI-Proofreader"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _revision_attrs(node: OxmlElement, rev_id: int) -> None:
    """统一设置修订节点的公共属性"""
    node.set(qn("w:id"),     str(rev_id))
    node.set(qn("w:author"), AUTHOR)
    node.set(qn("w:date"),   _utc_now())


def _make_run(text: str, is_del: bool, rpr_elem=None) -> OxmlElement:
    """
    创建 w:r 文字运行节点。
    is_del=True  → 使用 w:delText（放在 w:del 内）
    is_del=False → 使用 w:t      （放在 w:ins 内）
    rpr_elem: 可选的 w:rPr 元素，用于继承原始样式
    """
    r = OxmlElement("w:r")
    if rpr_elem is not None:
        r.append(deepcopy(rpr_elem))
    t = OxmlElement("w:delText" if is_del else "w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


def make_del_node(text: str, rev_id: int, rpr_elem=None) -> OxmlElement:
    """创建 w:del 删除修订节点"""
    node = OxmlElement("w:del")
    _revision_attrs(node, rev_id)
    node.append(_make_run(text, is_del=True, rpr_elem=rpr_elem))
    return node


def make_ins_node(text: str, rev_id: int, rpr_elem=None) -> OxmlElement:
    """创建 w:ins 插入修订节点"""
    node = OxmlElement("w:ins")
    _revision_attrs(node, rev_id)
    node.append(_make_run(text, is_del=False, rpr_elem=rpr_elem))
    return node


def new_rev_id() -> int:
    """生成不重复的修订ID（Word 要求唯一正整数，范围 1 ~ 0x7FFFFFFF）"""
    return uuid.uuid4().int % 0x7FFFFFFF + 1


def enable_track_changes(settings_element) -> None:
    """
    在文档 settings.xml 中开启 trackChanges。
    settings_element = doc.settings.element
    """
    # 检查是否已存在，避免重复添加
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    existing = settings_element.find(f"{{{ns}}}trackChanges")
    if existing is None:
        tc = OxmlElement("w:trackChanges")
        settings_element.insert(0, tc)
