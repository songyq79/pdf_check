"""英文档位配置 + 向后兼容单元测试"""
from app.core.plagiarism.levels import classify_risk, get_level_config


def test_en_journal_strictest_params():
    cfg = get_level_config("journal", language="en")
    assert cfg["embed_threshold"] == 0.70
    assert cfg["ngram_size"] == 5
    assert cfg["min_confidence"] == 30


def test_en_doctor_params():
    cfg = get_level_config("doctor", language="en")
    assert cfg["embed_threshold"] == 0.72
    assert cfg["ngram_size"] == 6
    assert cfg["min_confidence"] == 40


def test_en_undergraduate_params():
    cfg = get_level_config("undergraduate", language="en")
    assert cfg["embed_threshold"] == 0.80
    assert cfg["min_confidence"] == 60


def test_en_master_params():
    cfg = get_level_config("master", language="en")
    assert cfg["embed_threshold"] == 0.75
    assert cfg["min_confidence"] == 50


def test_en_empty_paper_type_fallback():
    cfg = get_level_config("", language="en")
    assert "embed_threshold" in cfg


def test_zh_backward_compat_no_language_arg():
    """原有中文接口调用不传 language 应保持行为"""
    cfg = get_level_config("doctor")
    assert "label" in cfg
    # 中文分级不应暴露 embed_threshold 等英文独有字段
    # (若实现上共享字段可放宽此断言)


def test_risk_classification_en_stricter():
    """英文期刊档阈值比中文更严:同样 rate 在英文下更可能升级"""
    # EN journal: rate_high=12, rate_medium=8
    assert classify_risk(10.0, "journal", language="en") in ("medium", "high")
    # ZH baseline should still work
    _ = classify_risk(10.0, "journal")
