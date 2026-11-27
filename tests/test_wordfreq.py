# AC#4: pytest -q passes across tests/test_wordfreq.py.
# Covers tie-breaking (sort by (-count, word)) and CLI behaviour: default stdin,
# '-' as path, --case-sensitive, --top, --min-len, --json, trailing newlines on
# TSV and --json output, python -m wordfreq, and exit code 2 with stderr on
# invalid arguments or a missing file.
import io
import json
import subprocess
import sys

import pytest

from wordfreq.cli import count_words, format_table, main


def run_main(argv, stdin_text, monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
    rc = main(argv)
    captured = capsys.readouterr()
    return rc, captured


# --- count_words: tie-breaking ---------------------------------------------

def test_count_words_tied_counts_sorted_by_word_ascending():
    result = count_words("zeta alpha beta alpha beta")
    assert result == [("alpha", 2), ("beta", 2), ("zeta", 1)]


def test_count_words_higher_count_sorted_before_lower_count():
    result = count_words("zeta zeta zeta alpha")
    assert result[0] == ("zeta", 3)


def test_count_words_all_tied_sorted_by_word_ascending():
    result = count_words("c b a")
    assert result == [("a", 1), ("b", 1), ("c", 1)]


def test_count_words_tie_break_is_case_sensitive_when_ignore_case_false():
    result = count_words("hello Hello", ignore_case=False)
    assert result == [("Hello", 1), ("hello", 1)]


# --- count_words: CLI-adjacent core behaviour -------------------------------

def test_count_words_default_lowercases_tokens():
    assert count_words("Hello HELLO") == [("hello", 2)]


def test_count_words_extracts_alnum_tokens_only():
    result = count_words("hello, world! 42-x_y")
    assert sorted(word for word, _ in result) == ["42", "hello", "world", "x", "y"]


def test_count_words_min_len_filters_short_words():
    result = count_words("a bb ccc dddd", min_len=3)
    assert result == [("ccc", 1), ("dddd", 1)]


def test_count_words_top_limits_results():
    assert count_words("a a b", top=1) == [("a", 2)]


def test_count_words_top_zero_returns_empty():
    assert count_words("a a b", top=0) == []


# --- format_table -----------------------------------------------------------

def test_format_table_rows_joined_with_tab_and_newline():
    assert format_table([("a", 2), ("b", 1)]) == "a\t2\nb\t1"


def test_format_table_empty_input_returns_empty_string():
    assert format_table([]) == ""


# --- main: default stdin and '-' --------------------------------------------

def test_main_default_reads_stdin_returns_zero(monkeypatch, capsys):
    rc, _ = run_main([], "a b a\n", monkeypatch, capsys)
    assert rc == 0


def test_main_default_reads_stdin_prints_tsv(monkeypatch, capsys):
    _, captured = run_main([], "a b a\n", monkeypatch, capsys)
    assert captured.out == "a\t2\nb\t1\n"


def test_main_dash_path_reads_stdin(monkeypatch, capsys):
    _, captured = run_main(["-"], "a b a\n", monkeypatch, capsys)
    assert captured.out == "a\t2\nb\t1\n"


def test_main_tie_break_output_sorted_by_word(monkeypatch, capsys):
    _, captured = run_main([], "zeta alpha alpha beta beta\n", monkeypatch, capsys)
    assert captured.out == "alpha\t2\nbeta\t2\nzeta\t1\n"


# --- main: flags ------------------------------------------------------------

def test_main_case_sensitive_flag_preserves_case(monkeypatch, capsys):
    _, captured = run_main(["--case-sensitive"], "Hello hello\n", monkeypatch, capsys)
    assert captured.out == "Hello\t1\nhello\t1\n"


def test_main_top_flag_limits_output(monkeypatch, capsys):
    _, captured = run_main(["--top", "1"], "a a b\n", monkeypatch, capsys)
    assert captured.out == "a\t2\n"


def test_main_min_len_flag_filters_short_words(monkeypatch, capsys):
    _, captured = run_main(["--min-len", "2"], "a bb ccc\n", monkeypatch, capsys)
    assert captured.out == "bb\t1\nccc\t1\n"


def test_main_json_flag_output_ends_with_newline(monkeypatch, capsys):
    _, captured = run_main(["--json"], "a b a\n", monkeypatch, capsys)
    assert captured.out.endswith("\n")


def test_main_json_flag_output_is_valid_json(monkeypatch, capsys):
    _, captured = run_main(["--json"], "a b a\n", monkeypatch, capsys)
    json.loads(captured.out)


def test_main_tsv_output_ends_with_newline(monkeypatch, capsys):
    _, captured = run_main([], "a\n", monkeypatch, capsys)
    assert captured.out.endswith("\n")


def test_main_empty_tsv_output_prints_nothing(monkeypatch, capsys):
    rc, captured = run_main([], "", monkeypatch, capsys)
    assert captured.out == ""


def test_main_empty_tsv_output_returns_zero(monkeypatch, capsys):
    rc, _ = run_main([], "", monkeypatch, capsys)
    assert rc == 0


# --- main: errors -----------------------------------------------------------

@pytest.mark.parametrize(
    "argv",
    [
        ["--top", "-1"],
        ["--min-len", "0"],
        ["--no-such-flag"],
    ],
    ids=["negative-top", "zero-min-len", "unknown-flag"],
)
def test_main_invalid_arguments_returns_two(argv, monkeypatch, capsys):
    rc, _ = run_main(argv, "a\n", monkeypatch, capsys)
    assert rc == 2


@pytest.mark.parametrize(
    "argv",
    [
        ["--top", "-1"],
        ["--min-len", "0"],
        ["--no-such-flag"],
    ],
    ids=["negative-top", "zero-min-len", "unknown-flag"],
)
def test_main_invalid_arguments_writes_stderr(argv, monkeypatch, capsys):
    _, captured = run_main(argv, "a\n", monkeypatch, capsys)
    assert captured.err != ""


def test_main_missing_file_returns_two(tmp_path, monkeypatch, capsys):
    rc, _ = run_main([str(tmp_path / "missing.txt")], "", monkeypatch, capsys)
    assert rc == 2


def test_main_missing_file_writes_stderr(tmp_path, monkeypatch, capsys):
    _, captured = run_main([str(tmp_path / "missing.txt")], "", monkeypatch, capsys)
    assert captured.err != ""


# --- python -m wordfreq -----------------------------------------------------

def test_python_m_wordfreq_reads_piped_stdin_exit_zero():
    proc = subprocess.run(
        [sys.executable, "-m", "wordfreq"],
        input="a b a\n",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0


def test_python_m_wordfreq_reads_piped_stdin_prints_tsv():
    proc = subprocess.run(
        [sys.executable, "-m", "wordfreq"],
        input="a b a\n",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.stdout == "a\t2\nb\t1\n"


def test_python_m_wordfreq_missing_file_returns_two(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "wordfreq", str(tmp_path / "missing.txt")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 2


def test_python_m_wordfreq_missing_file_writes_stderr(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "wordfreq", str(tmp_path / "missing.txt")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.stderr != ""
