"""参考文献剥离 + 引文标注清除单元测试(精度增强 #1)"""
from app.core.plagiarism.reference_stripper import (
    preprocess_english,
    strip_inline_citations,
    strip_references,
)


def test_strip_references_section():
    text = (
        "We propose a novel approach.\n\n"
        "References\n"
        "[1] Foo et al. 2020\n"
        "[2] Bar 2021\n"
    )
    out = strip_references(text)
    assert "References" not in out
    assert "Foo et al" not in out
    assert "We propose a novel approach" in out


def test_strip_references_bibliography_variant():
    text = "Main body.\n\nBibliography\n1. A. B. Work, 2020."
    out = strip_references(text)
    assert "Bibliography" not in out
    assert "Main body" in out


def test_strip_references_chinese_variant():
    text = "正文内容。\n\n参考文献\n[1] 张三, 2020."
    out = strip_references(text)
    assert "参考文献" not in out
    assert "正文内容" in out


def test_strip_inline_numeric_citations():
    text = "As shown [12], we find [12, 15] and earlier work [12-18]."
    out = strip_inline_citations(text)
    assert "[12" not in out
    assert "[15" not in out
    assert "As shown" in out
    assert "we find" in out


def test_strip_inline_author_year_citations():
    text = "Prior work (Smith, 2020) and (Smith et al., 2020; Jones, 2021) showed ..."
    out = strip_inline_citations(text)
    assert "Smith" not in out
    assert "Jones" not in out
    assert "Prior work" in out
    assert "showed" in out


def test_preprocess_preserves_original_content():
    """纯原创文本应保持不变(无 References、无引文)"""
    text = "This is a purely original paragraph with no citations or references section."
    assert preprocess_english(text).strip() == text.strip()
