"""语言检测单元测试"""
from app.core.plagiarism.language_detector import detect_language


def test_detect_pure_chinese():
    text = "这是一段完全由中文字符组成的测试文本，用来验证语言检测功能的准确性。" * 3
    assert detect_language(text) == "zh"


def test_detect_pure_english():
    text = (
        "This is an English sample designed to verify the language detector. "
        "It should reliably classify this paragraph as English based on statistical cues."
    )
    assert detect_language(text) == "en"


def test_detect_mixed_chinese_dominant():
    """中英混合但中文占绝对主导 → zh"""
    text = (
        "本研究提出一种新的论文查重方法，通过语义分析识别潜在的抄袭内容。"
        "实验结果表明，该方法在多个公开数据集上均取得了显著的性能提升。"
        "与现有方法相比，本文方法在准确率和召回率方面均有明显改进。"
        "我们使用 BERT 模型进行语义编码，效果良好。"
    ) * 2
    assert detect_language(text) == "zh"


def test_detect_short_text_falls_back():
    """短文本也应返回 zh/en 之一,不应抛异常"""
    result = detect_language("hello")
    assert result in ("zh", "en")


def test_detect_empty_string():
    assert detect_language("") in ("zh", "en")
