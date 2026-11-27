# AC#1: count_words raises ValueError('min_len must be >= 1') when min_len < 1,
# and ValueError('top must be >= 0') when top < 0. count_words honors top=0
# (no entries returned) and limits the result to at most `top` entries.

import pytest

from wordfreq.cli import count_words

SAMPLE_TEXT = "alpha beta gamma delta alpha beta alpha"


@pytest.mark.parametrize("min_len", [0, -1, -5], ids=["zero", "minus_one", "minus_five"])
def test_count_words_min_len_below_one_raises_value_error(min_len):
    with pytest.raises(ValueError) as excinfo:
        count_words(SAMPLE_TEXT, min_len=min_len)
    assert str(excinfo.value) == "min_len must be >= 1"


@pytest.mark.parametrize("top", [-1, -10], ids=["minus_one", "minus_ten"])
def test_count_words_top_negative_raises_value_error(top):
    with pytest.raises(ValueError) as excinfo:
        count_words(SAMPLE_TEXT, top=top)
    assert str(excinfo.value) == "top must be >= 0"


def test_count_words_top_zero_returns_no_entries():
    result = count_words(SAMPLE_TEXT, top=0)
    assert len(result) == 0


def test_count_words_top_limit_caps_result_length():
    result = count_words(SAMPLE_TEXT, top=2)
    assert len(result) == 2
