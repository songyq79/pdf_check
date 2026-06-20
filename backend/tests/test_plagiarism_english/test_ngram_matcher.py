"""N-gram 硬命中单元测试(精度增强 #2)"""
from app.core.plagiarism import ngram_matcher


def test_consecutive_6_word_overlap_hits():
    user = "the quick brown fox jumps over the lazy dog"
    cand = "In corpora the quick brown fox jumps over the lazy dog appears"
    hit = ngram_matcher.check(user, cand, n=6)
    assert hit is not None
    assert hit.overlap_words >= 6


def test_only_5_words_consecutive_misses_at_n6():
    user = "alpha beta gamma delta epsilon zeta"
    cand = "nothing alpha beta gamma delta epsilon matches here"
    # user 连续 5 词 "alpha beta gamma delta epsilon" 在 cand 中,但 n=6 不达
    hit = ngram_matcher.check(user, cand, n=6)
    assert hit is None


def test_case_and_punctuation_insensitive():
    user = "THE Quick, Brown Fox Jumps Over the lazy DOG!"
    cand = "the quick brown fox jumps over the lazy dog"
    hit = ngram_matcher.check(user, cand, n=6)
    assert hit is not None


def test_returns_longest_overlap():
    """重合段延伸到 8 词应返回 overlap_words=8"""
    user = "a b c d e f g h i"
    cand = "x a b c d e f g h i y"
    hit = ngram_matcher.check(user, cand, n=6)
    assert hit is not None
    assert hit.overlap_words == 9


def test_no_overlap_returns_none():
    user = "completely different words here"
    cand = "some other unrelated content appears"
    assert ngram_matcher.check(user, cand, n=6) is None


def test_short_inputs_return_none():
    assert ngram_matcher.check("too short", "doesn't matter either", n=6) is None


def test_journal_level_5gram():
    user = "alpha beta gamma delta epsilon zeta"
    cand = "alpha beta gamma delta epsilon extra"
    hit = ngram_matcher.check(user, cand, n=5)
    assert hit is not None
    assert hit.overlap_words >= 5
