"""
文档解析 + 语义分句 + 文本清洗
支持 .docx / .txt / .pdf
"""
from __future__ import annotations
import re
from typing import List, Tuple


def parse_file(file_path: str) -> str:
    """解析文件，返回纯文本"""
    lower = file_path.lower()
    if lower.endswith(".docx"):
        return _parse_docx(file_path)
    elif lower.endswith(".txt"):
        return _parse_txt(file_path)
    elif lower.endswith(".pdf"):
        return _parse_pdf(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {file_path}")


def _parse_docx(path: str) -> str:
    from docx import Document
    from app.services.docx_normalizer import normalize_docx
    path = str(normalize_docx(path))
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _parse_pdf(path: str) -> str:
    from app.services.pdf_extractor import extract_text_from_pdf
    return extract_text_from_pdf(path)


def _parse_txt(path: str) -> str:
    for enc in ("utf-8", "gbk", "utf-16"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError("无法识别文件编码")


def clean_text(text: str) -> str:
    """基础清洗：去除多余空白，统一标点"""
    text = re.sub(r"\s+", " ", text)
    # 全角空格转普通空格
    text = text.replace("\u3000", " ")
    return text.strip()


def segment_sentences(text: str, min_len: int = 20, max_len: int = 150) -> List[Tuple[str, int, int]]:
    """
    语义分句，返回 [(句子, start_pos, end_pos), ...]
    按句号/问号/感叹号切分，合并过短片段
    """
    # 切分点：中英文句末标点
    pattern = re.compile(r"[。！？!?]+")
    sentences: List[Tuple[str, int, int]] = []
    last = 0
    for m in pattern.finditer(text):
        end = m.end()
        seg = text[last:end].strip()
        if seg:
            sentences.append((seg, last, end))
        last = end
    # 末尾剩余
    if last < len(text):
        seg = text[last:].strip()
        if seg:
            sentences.append((seg, last, len(text)))

    # 合并过短片段
    merged: List[Tuple[str, int, int]] = []
    buf_text, buf_start, buf_end = "", 0, 0
    for seg, s, e in sentences:
        if not buf_text:
            buf_text, buf_start, buf_end = seg, s, e
        else:
            combined = buf_text + seg
            if len(buf_text) < min_len:
                buf_text, buf_end = combined, e
            else:
                merged.append((buf_text, buf_start, buf_end))
                buf_text, buf_start, buf_end = seg, s, e
    if buf_text:
        merged.append((buf_text, buf_start, buf_end))

    # 过滤过短片段
    return [(t, s, e) for t, s, e in merged if len(t) >= min_len]
