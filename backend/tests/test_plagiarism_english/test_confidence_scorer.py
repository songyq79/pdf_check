"""置信度评分单元测试(精度增强 #7)"""
from app.core.plagiarism import confidence_scorer


def test_ngram_hit_plus_direct_copy_high():
    # ngram 50 + embed 0.92 (≥0.90) 30 + direct_copy 30 = 110 → clamp 100
    assert confidence_scorer.score(True, 0.92, "direct_copy") == 100


def test_embed_only_paraphrase_mid_band():
    # ngram 0 + embed 0.78 (0.75-0.80) 10 + paraphrase 20 = 30
    assert confidence_scorer.score(False, 0.78, "paraphrase") == 30


def test_embed_082_paraphrase():
    # 0 + 20 (0.80-0.90) + 20 paraphrase = 40
    assert confidence_scorer.score(False, 0.82, "paraphrase") == 40


def test_original_verdict_penalty():
    # 0 + 10 + (-20) = -10 → clamp 0
    assert confidence_scorer.score(False, 0.76, "original") == 0


def test_below_embed_threshold():
    # embed 0.50 不加分;paraphrase +20 = 20
    assert confidence_scorer.score(False, 0.50, "paraphrase") == 20


def test_ngram_hit_strong_signal_alone():
    # ngram 50 + embed 0.72 (< 0.75 不加分) + 空 verdict = 50
    assert confidence_scorer.score(True, 0.72, "") == 50


def test_common_knowledge_small_bonus():
    # 0 + 0 (embed 0.60) + 5 = 5
    assert confidence_scorer.score(False, 0.60, "common_knowledge") == 5


def test_output_bounded_0_to_100():
    assert 0 <= confidence_scorer.score(True, 1.0, "direct_copy") <= 100
    assert 0 <= confidence_scorer.score(False, 0.0, "original") <= 100
