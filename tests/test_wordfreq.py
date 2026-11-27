"""Unit and CLI tests for the wordfreq package."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from wordfreq.cli import count_words, format_table, main

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_module(*args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wordfreq", *args],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )


# --- count_words: ranking and tie-breaking -------------------------------


def test_count_words_basic_ranking() -> None:
    text = "Apple banana apple, cherry! Banana apple."
    assert count_words(text) == [("apple", 3), ("banana", 2), ("cherry", 1)]


def test_count_words_equal_counts_sorted_alphabetically() -> None:
    assert count_words("pear kiwi apple fig") == [
        ("apple", 1),
        ("fig", 1),
        ("kiwi", 1),
        ("pear", 1),
    ]


def test_count_words_tied_counts_break_ties_by_word() -> None:
    assert count_words("zeta alpha zeta alpha mu mu") == [
        ("alpha", 2),
        ("mu", 2),
        ("zeta", 2),
    ]


def test_count_words_higher_count_ranks_first() -> None:
    assert count_words("a b b c c c") == [("c", 3), ("b", 2), ("a", 1)]


def test_count_words_result_independent_of_token_order() -> None:
    tokens = ["delta", "alpha", "charlie", "alpha", "bravo", "delta"]
    forward = count_words(" ".join(tokens))
    backward = count_words(" ".join(reversed(tokens)))
    expected = [("alpha", 2), ("delta", 2), ("bravo", 1), ("charlie", 1)]
    assert forward == expected
    assert backward == expected


# --- count_words: case handling ------------------------------------------


def test_count_words_lowercases_by_default() -> None:
    assert count_words("Hello HELLO hello") == [("hello", 3)]


def test_count_words_ignore_case_false_preserves_case() -> None:
    assert count_words("Hello hello HELLO", ignore_case=False) == [
        ("HELLO", 1),
        ("Hello", 1),
        ("hello", 1),
    ]


def test_count_words_ignore_case_false_counts_exact_matches() -> None:
    assert count_words("Hello Hello hello", ignore_case=False) == [
        ("Hello", 2),
        ("hello", 1),
    ]


# --- count_words: tokenisation, filtering and limits ---------------------


def test_count_words_splits_on_non_alphanumeric_characters() -> None:
    assert count_words("don't stop-go 42 4_2") == [
        ("2", 1),
        ("4", 1),
        ("42", 1),
        ("don", 1),
        ("go", 1),
        ("stop", 1),
        ("t", 1),
    ]


def test_count_words_ignores_non_ascii_letters() -> None:
    assert count_words("café") == [("caf", 1)]


def test_count_words_empty_text_returns_empty_list() -> None:
    assert count_words("") == []
    assert count_words("!!! ... ---") == []


def test_count_words_min_len_filters_short_words() -> None:
    assert count_words("a ab abc ab", min_len=2) == [("ab", 2), ("abc", 1)]


def test_count_words_top_limits_results() -> None:
    assert count_words("a a a b b c", top=2) == [("a", 3), ("b", 2)]


def test_count_words_top_zero_returns_empty_list() -> None:
    assert count_words("a b", top=0) == []


def test_count_words_top_larger_than_vocabulary_returns_all() -> None:
    assert count_words("a b", top=10) == [("a", 1), ("b", 1)]


@pytest.mark.parametrize("min_len", [0, -1])
def test_count_words_rejects_min_len_below_one(min_len: int) -> None:
    with pytest.raises(ValueError, match="min_len must be >= 1"):
        count_words("a", min_len=min_len)


def test_count_words_rejects_negative_top() -> None:
    with pytest.raises(ValueError, match="top must be >= 0"):
        count_words("a", top=-1)


# --- format_table --------------------------------------------------------


def test_format_table_tsv() -> None:
    assert format_table([("apple", 3), ("banana", 2)]) == "apple\t3\nbanana\t2"


def test_format_table_empty_returns_empty_string() -> None:
    assert format_table([]) == ""


def test_format_table_single_row_has_no_trailing_newline() -> None:
    assert format_table([("solo", 7)]) == "solo\t7"


# --- CLI: input sources --------------------------------------------------


def test_cli_reads_stdin_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("b a a\n"))
    assert main([]) == 0
    assert capsys.readouterr().out == "a\t2\nb\t1\n"


def test_cli_dash_reads_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("x y x"))
    assert main(["-"]) == 0
    assert capsys.readouterr().out == "x\t2\ny\t1\n"


def test_cli_top_and_min_len(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("to be or not to be that is the question", encoding="utf-8")
    rc = main([str(sample), "--min-len", "3", "--top", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.strip().splitlines() == ["not\t1", "question\t1"]


def test_cli_breaks_ties_alphabetically(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sample = tmp_path / "ties.txt"
    sample.write_text("pear kiwi pear kiwi apple", encoding="utf-8")
    assert main([str(sample)]) == 0
    assert capsys.readouterr().out == "kiwi\t2\npear\t2\napple\t1\n"


# --- CLI: --case-sensitive -----------------------------------------------


def test_cli_lowercases_by_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sample = tmp_path / "case.txt"
    sample.write_text("Go go GO go", encoding="utf-8")
    assert main([str(sample)]) == 0
    assert capsys.readouterr().out == "go\t4\n"


def test_cli_case_sensitive_preserves_case(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sample = tmp_path / "case.txt"
    sample.write_text("Go go GO go", encoding="utf-8")
    assert main([str(sample), "--case-sensitive"]) == 0
    assert capsys.readouterr().out == "go\t2\nGO\t1\nGo\t1\n"


# --- CLI: output formatting ----------------------------------------------


def test_cli_tsv_output_ends_with_single_newline(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("a b a"))
    assert main([]) == 0
    out = capsys.readouterr().out
    assert out == "a\t2\nb\t1\n"
    assert not out.endswith("\n\n")


def test_cli_empty_tsv_output_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("!!! ..."))
    assert main([]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_cli_json_output_is_array_with_trailing_newline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sample = tmp_path / "json.txt"
    sample.write_text("a b a", encoding="utf-8")
    assert main([str(sample), "--json"]) == 0
    out = capsys.readouterr().out
    assert out == '[{"word": "a", "count": 2}, {"word": "b", "count": 1}]\n'
    assert json.loads(out) == [{"word": "a", "count": 2}, {"word": "b", "count": 1}]


def test_cli_empty_json_output_is_empty_array(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert main(["--json"]) == 0
    assert capsys.readouterr().out == "[]\n"


# --- CLI: argument validation and errors ---------------------------------


@pytest.mark.parametrize(
    "args",
    [
        ["--top", "-1"],
        ["--min-len", "0"],
        ["--top", "abc"],
        ["--min-len"],
        ["--bogus"],
    ],
)
def test_cli_invalid_arguments_exit_2_with_stderr(
    args: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("a b"))
    rc = main(args)
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert captured.err.strip() != ""


def test_cli_reports_min_len_error_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("a"))
    assert main(["--min-len", "0"]) == 2
    assert "min_len must be >= 1" in capsys.readouterr().err


def test_cli_reports_top_error_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("a"))
    assert main(["--top", "-1"]) == 2
    assert "top must be >= 0" in capsys.readouterr().err


def test_cli_missing_file_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "does-not-exist.txt"
    rc = main([str(missing)])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert captured.err.strip() != ""


# --- python -m wordfreq --------------------------------------------------


def test_python_m_wordfreq_reads_stdin() -> None:
    result = run_module(stdin="b a a\n")
    assert result.returncode == 0
    assert result.stdout == "a\t2\nb\t1\n"
    assert result.stderr == ""


def test_python_m_wordfreq_json_output_has_trailing_newline() -> None:
    result = run_module("--json", stdin="hi hi")
    assert result.returncode == 0
    assert result.stdout == '[{"word": "hi", "count": 2}]\n'


def test_python_m_wordfreq_empty_output_writes_nothing() -> None:
    result = run_module(stdin="...")
    assert result.returncode == 0
    assert result.stdout == ""


def test_python_m_wordfreq_missing_file_exits_2(tmp_path: Path) -> None:
    result = run_module(str(tmp_path / "missing.txt"))
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() != ""


def test_python_m_wordfreq_invalid_argument_exits_2() -> None:
    result = run_module("--min-len", "0", stdin="a")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() != ""
