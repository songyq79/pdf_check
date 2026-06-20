"""
PDF 文本提取工具

仅处理文字版 PDF。扫描版(图片 PDF)会抛 PdfExtractionError,
由调用方转成对用户友好的 400 错误。
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber
from loguru import logger


class PdfExtractionError(Exception):
    """PDF 内容无法提取(空文档 / 扫描版 / 损坏)。"""


_CTRL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _extract_page_text(page) -> str:
    """用 extract_words 提取，强制加空格，解决学术 PDF 词语合并问题。"""
    try:
        words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False)
        if words:
            return " ".join(w["text"] for w in words)
    except Exception:
        pass
    return page.extract_text() or ""

# 有效内容阈值:少于该字数视作扫描版或无法解析
_MIN_VALID_CHARS = 50


def _clean_control_chars(text: str) -> str:
    """去除会污染 AI prompt 的控制字符,保留 \\n \\r \\t。"""
    return _CTRL_CHARS_RE.sub("", text)


def extract_text_from_pdf(file_path: Path | str) -> str:
    """
    从 PDF 提取纯文本。

    :param file_path: PDF 文件路径
    :return: 以 \\n 拼接的纯文本(已清洗控制字符)
    :raises PdfExtractionError: 文件打不开、提取为空或疑似扫描版
    """
    path = Path(file_path)

    try:
        parts: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = _extract_page_text(page)
                if page_text:
                    parts.append(page_text)
    except Exception as exc:
        logger.error(f"[pdf_extractor] 打开或解析 PDF 失败: {exc}")
        raise PdfExtractionError(f"PDF 解析失败: {exc}") from exc

    text = "\n".join(parts)
    text = _clean_control_chars(text)

    if len(text.strip()) < _MIN_VALID_CHARS:
        logger.warning(
            f"[pdf_extractor] 提取文本过短 ({len(text.strip())} 字),疑似扫描版: {path.name}"
        )
        raise PdfExtractionError(
            "PDF 内容为空或为扫描版,请上传文字版 PDF 或 .docx 文件"
        )

    logger.info(f"[pdf_extractor] 提取成功: {path.name} → {len(text)} 字符")
    return text
