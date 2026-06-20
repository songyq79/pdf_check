"""
Word 修订节点生成工具

生成符合 OOXML 规范的 w:del / w:ins 修订节点，
用于在 Word 中实现 Track Changes（修订模式）。

同时支持 Word 批注（comments）功能，为每处修改添加修改原因说明。

关键原则：
- 每个修订节点必须有唯一的 w:id（正整数）
- w:del 内用 w:delText，w:ins 内用 w:t
- 需要保留原始 run 的字体/样式属性（w:rPr）
- 批注通过 word/comments.xml 存储，段落中用 commentRangeStart/End 标记范围
"""

import uuid
import logging
from copy import deepcopy
from datetime import datetime, timezone
from lxml import etree

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

logger = logging.getLogger(__name__)

AUTHOR = "AI-Proofreader"

# Word comments.xml 的 content type
_COMMENTS_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
# comments relationship type
_COMMENTS_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _revision_attrs(node: OxmlElement, rev_id: int) -> None:
    """统一设置修订节点的公共属性"""
    node.set(qn("w:id"),     str(rev_id))
    node.set(qn("w:author"), AUTHOR)
    node.set(qn("w:date"),   _utc_now())


def _sanitize_rpr(rpr_elem):
    """
    深拷贝 rPr 并剥除不应该被继承到修订节点里的属性：
    - w:rStyle val="CommentReference"：批注引用样式，绝不能继承到 w:ins/w:del 内
    - w:commentReference：直接的批注引用，同理
    """
    cloned = deepcopy(rpr_elem)
    # 剥离 rStyle=CommentReference
    for rstyle in cloned.findall(qn("w:rStyle")):
        val = rstyle.get(qn("w:val"))
        if val == "CommentReference":
            cloned.remove(rstyle)
    # 剥离 commentReference（几乎不会出现在 rPr 里，保险）
    for cref in cloned.findall(qn("w:commentReference")):
        cloned.remove(cref)
    return cloned


def _make_run(text: str, is_del: bool, rpr_elem=None) -> OxmlElement:
    """
    创建 w:r 文字运行节点。
    is_del=True  → 使用 w:delText（放在 w:del 内）
    is_del=False → 使用 w:t      （放在 w:ins 内）
    rpr_elem: 可选的 w:rPr 元素，用于继承原始样式
    """
    r = OxmlElement("w:r")
    if rpr_elem is not None:
        r.append(_sanitize_rpr(rpr_elem))
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


# ─────────────────────────────────────────────────────────────
# Word 批注（Comments）支持
# ─────────────────────────────────────────────────────────────

_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_COMMENTS_XML_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:comments xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"'
    ' xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
    ' xmlns:o="urn:schemas-microsoft-com:office:office"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    ' xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
    ' xmlns:v="urn:schemas-microsoft-com:vml"'
    ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
    ' xmlns:w10="urn:schemas-microsoft-com:office:word"'
    ' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ' xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"'
    ' xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"'
    ' xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"'
    ' xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"'
    ' xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"'
    ' mc:Ignorable="w14 wp14">'
    '</w:comments>'
)


def _get_or_create_comments_part(doc):
    """
    获取或创建文档的 comments.xml part。
    返回 comments 根元素（lxml Element）。
    """
    from docx.opc.part import Part
    from docx.opc.packuri import PackURI

    document_part = doc.part

    # 检查是否已有 comments part
    for rel in document_part.rels.values():
        if rel.reltype == _COMMENTS_REL_TYPE:
            comments_part = rel.target_part
            return etree.fromstring(comments_part.blob)

    # 不存在，创建新的
    return etree.fromstring(_COMMENTS_XML_TEMPLATE.encode("utf-8"))


def _save_comments_part(doc, comments_elem):
    """
    将 comments 元素保存回文档的 comments.xml part。
    如果 part 不存在则创建并关联。

    关键：新建 part 必须通过 package 正式路径让其进入 package._parts，
    否则 [Content_Types].xml 不会写入 Override，Word 打开时报
    "内容有问题"。
    """
    from docx.opc.part import Part
    from docx.opc.packuri import PackURI

    document_part = doc.part
    package = document_part.package
    blob = etree.tostring(comments_elem, xml_declaration=True, encoding="UTF-8", standalone=True)

    # 1) 已存在：直接替换 blob
    for rel in document_part.rels.values():
        if rel.reltype == _COMMENTS_REL_TYPE:
            rel.target_part._blob = blob
            return

    # 2) 新建：创建 Part 并建立 relationship
    comments_uri = PackURI("/word/comments.xml")
    comments_part = Part(comments_uri, _COMMENTS_CONTENT_TYPE, blob, package)

    # relate_to 会把 rel 写进 document_part.rels，
    # 打包时 iter_parts 会递归到 comments_part，Override 随之写入。
    document_part.relate_to(comments_part, _COMMENTS_REL_TYPE)


def ensure_comments_content_type(docx_path) -> bool:
    """
    打包后兜底：若 docx 里含 word/comments.xml 却在 [Content_Types].xml 中
    缺少对应的 Override，则原地修补 zip。

    返回是否执行过修补。
    """
    import zipfile
    import shutil
    import tempfile
    from pathlib import Path

    docx_path = Path(docx_path)
    if not docx_path.exists():
        return False

    try:
        with zipfile.ZipFile(str(docx_path), "r") as zf:
            names = zf.namelist()
            if "word/comments.xml" not in names:
                return False
            if "[Content_Types].xml" not in names:
                return False
            ct_xml = zf.read("[Content_Types].xml").decode("utf-8")
    except zipfile.BadZipFile:
        logger.warning(f"ensure_comments_content_type: 损坏的 zip: {docx_path}")
        return False

    if _COMMENTS_CONTENT_TYPE in ct_xml:
        return False  # 已有 Override，无需修补

    # 注入 Override
    override_tag = (
        f'<Override PartName="/word/comments.xml" '
        f'ContentType="{_COMMENTS_CONTENT_TYPE}"/>'
    )
    if "</Types>" not in ct_xml:
        logger.warning("ensure_comments_content_type: [Content_Types].xml 缺少 </Types>")
        return False
    patched_ct = ct_xml.replace("</Types>", override_tag + "</Types>")

    # 原地替换：复制到临时文件后改名
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".docx", dir=str(docx_path.parent))
    import os
    os.close(tmp_fd)
    try:
        with zipfile.ZipFile(str(docx_path), "r") as zin, \
             zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    data = patched_ct.encode("utf-8")
                zout.writestr(item, data)
        shutil.move(tmp_path, str(docx_path))
        logger.info(f"ensure_comments_content_type: 已修补 {docx_path.name} 的 [Content_Types].xml")
        return True
    except Exception as e:
        logger.error(f"ensure_comments_content_type: 修补失败 {e}")
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return False


def add_comment_to_element(comments_elem, comment_id, text):
    """
    向 comments 根元素中添加一条批注。

    Args:
        comments_elem: comments.xml 的根元素
        comment_id: 批注 ID（正整数）
        text: 批注文本内容（支持多行，每行一个 w:p）
    """
    comment = OxmlElement("w:comment")
    comment.set(qn("w:id"), str(comment_id))
    comment.set(qn("w:author"), AUTHOR)
    comment.set(qn("w:date"), _utc_now())
    comment.set(qn("w:initials"), "AI")

    # 批注内容：每行一个 w:p 段落（Word 不支持 w:t 内换行）
    lines = text.split("\n") if "\n" in text else [text]
    for line in lines:
        p = OxmlElement("w:p")
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.set(qn("xml:space"), "preserve")
        t.text = line
        r.append(t)
        p.append(r)
        comment.append(p)

    comments_elem.append(comment)


def make_comment_range_start(comment_id):
    """创建 w:commentRangeStart 节点"""
    node = OxmlElement("w:commentRangeStart")
    node.set(qn("w:id"), str(comment_id))
    return node


def make_comment_range_end(comment_id):
    """创建 w:commentRangeEnd 节点"""
    node = OxmlElement("w:commentRangeEnd")
    node.set(qn("w:id"), str(comment_id))
    return node


def make_comment_reference(comment_id):
    """
    创建批注引用 run：w:r > w:rPr > w:rStyle + w:commentReference
    这个 run 放在 commentRangeEnd 之后，Word 用它来显示批注气泡。
    """
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    style = OxmlElement("w:rStyle")
    style.set(qn("w:val"), "CommentReference")
    rpr.append(style)
    r.append(rpr)

    ref = OxmlElement("w:commentReference")
    ref.set(qn("w:id"), str(comment_id))
    r.append(ref)
    return r
