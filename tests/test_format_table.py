# AC#2: format_table formats rows as word\tcount lines separated by \n and returns '' for empty input
#
# Rows are assumed to be (word, count) pairs. Output must be word<TAB>count
# lines joined with "\n", with no trailing newline. Empty input returns "".

import pytest

from wordfreq.cli import format_table


def test_format_table_multiple_rows_joined_with_newline_tab_separated():
    rows = [("the", 3), ("cat", 1)]

    result = format_table(rows)

    assert result == "the\t3\ncat\t1"


def test_format_table_single_row_has_no_trailing_newline():
    rows = [("the", 3)]

    result = format_table(rows)

    assert result == "the\t3"
    assert not result.endswith("\n")


def test_format_table_multiple_rows_has_no_trailing_newline():
    rows = [("a", 10), ("b", 2), ("c", 1)]

    result = format_table(rows)

    assert not result.endswith("\n")


def test_format_table_empty_input_returns_empty_string():
    result = format_table([])

    assert result == ""


@pytest.mark.parametrize(
    "rows,expected",
    [
        pytest.param([("hello", 5)], "hello\t5", id="one-row"),
        pytest.param([("x", 1), ("y", 2)], "x\t1\ny\t2", id="two-rows"),
        pytest.param([], "", id="empty-input"),
    ],
)
def test_format_table_various_inputs_matches_expected_format(rows, expected):
    assert format_table(rows) == expected
