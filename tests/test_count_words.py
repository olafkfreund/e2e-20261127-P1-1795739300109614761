# Acceptance criterion (AC#1): count_words extracts tokens, lowercases by default,
# preserves case, filters by min_len, and sorts by (-count, word).
#
# Subtask: count-words-tokens-case-sort
# Verify count_words extracts [A-Za-z0-9]+ tokens, lowercases by default, preserves
# case with ignore_case=False, filters by min_len, and sorts by (-count, word).

import pytest

from wordfreq.cli import count_words


def test_count_words_extracts_alnum_tokens_from_punctuated_text():
    result = count_words("Hello, world! foo_bar 42")

    assert set(result) == {
        ("hello", 1),
        ("world", 1),
        ("foo", 1),
        ("bar", 1),
        ("42", 1),
    }


def test_count_words_ignores_non_alnum_characters_as_separators():
    result = count_words("alpha-beta.gamma/delta")

    assert set(result) == {
        ("alpha", 1),
        ("beta", 1),
        ("gamma", 1),
        ("delta", 1),
    }


def test_count_words_lowercases_tokens_by_default():
    result = count_words("Apple apple APPLE")

    assert result == [("apple", 3)]


def test_count_words_preserves_case_when_ignore_case_false():
    result = count_words("Apple apple APPLE", ignore_case=False)

    assert set(result) == {
        ("Apple", 1),
        ("apple", 1),
        ("APPLE", 1),
    }


def test_count_words_filters_tokens_shorter_than_min_len():
    result = count_words("a bb ccc dddd", min_len=3)

    assert set(result) == {
        ("ccc", 1),
        ("dddd", 1),
    }


def test_count_words_sorts_by_descending_count():
    result = count_words("b a b c a b")

    assert result == [("b", 3), ("a", 2), ("c", 1)]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("zebra apple mango", [("apple", 1), ("mango", 1), ("zebra", 1)]),
        ("beta alpha beta alpha gamma", [("alpha", 2), ("beta", 2), ("gamma", 1)]),
    ],
    ids=["all_ties_sorted_alphabetically", "tied_counts_sorted_by_word"],
)
def test_count_words_sorts_ties_by_word_ascending(text, expected):
    result = count_words(text)

    assert result == expected
