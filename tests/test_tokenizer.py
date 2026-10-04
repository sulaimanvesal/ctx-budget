"""Tests for the offline token estimator."""

from ctx_budget.tokenizer import estimate_tokens


def test_empty_is_zero():
    assert estimate_tokens("") == 0


def test_scales_with_length():
    short = estimate_tokens("hello world")
    long = estimate_tokens("hello world " * 100)
    assert 0 < short < long


def test_typical_prose_near_four_chars_per_token():
    text = (
        "The quick brown fox jumps over the lazy dog. "
        "Pack my box with five dozen liquor jugs. "
    ) * 20
    tokens = estimate_tokens(text)
    ratio = len(text) / tokens
    assert 2.5 < ratio < 6.0, f"ratio {ratio} outside plausible range"


def test_deterministic():
    text = "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)"
    assert estimate_tokens(text) == estimate_tokens(text)


def test_minimum_one_for_nonempty():
    assert estimate_tokens("x") >= 1


def test_whitespace_heavy_text_is_cheaper_per_char():
    dense = "word" * 250      # 1000 chars, no whitespace
    sparse = "word " * 200    # 1000 chars, whitespace-separated
    assert estimate_tokens(sparse) < estimate_tokens(dense)
