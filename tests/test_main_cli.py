# AC#3: main reads stdin by default, honors flags, final newline on TSV and --json, returns 0
# Subtask: main-stdin-flags-output
# Verify main reads stdin by default and for '-', honors --case-sensitive, --top, --min-len,
# --json, and terminates TSV/JSON output with a final newline (nothing for empty TSV).

import io
import json
import sys

import pytest

from wordfreq.cli import main


def _feed_stdin(monkeypatch, text):
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))


def test_main_reads_stdin_by_default_returns_zero(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "apple banana apple\n")
    rc = main([])
    assert rc == 0


def test_main_reads_stdin_by_default_outputs_words(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "apple banana apple\n")
    main([])
    out = capsys.readouterr().out
    assert "apple" in out


def test_main_dash_argument_reads_stdin_returns_zero(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "cherry cherry\n")
    rc = main(["-"])
    assert rc == 0


def test_main_dash_argument_reads_stdin_outputs_words(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "cherry cherry\n")
    main(["-"])
    out = capsys.readouterr().out
    assert "cherry" in out


def test_main_tsv_output_ends_with_final_newline(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "apple banana apple\n")
    main([])
    out = capsys.readouterr().out
    assert out.endswith("\n")


def test_main_json_output_ends_with_final_newline(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "apple banana apple\n")
    main(["--json"])
    out = capsys.readouterr().out
    assert out.endswith("\n")


def test_main_json_flag_output_is_parseable_json(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "apple banana apple\n")
    main(["--json"])
    out = capsys.readouterr().out
    json.loads(out)


def test_main_empty_stdin_tsv_outputs_nothing(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "")
    rc = main([])
    out = capsys.readouterr().out
    assert out == ""
    assert rc == 0


def test_main_case_sensitive_flag_returns_zero(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "Apple apple APPLE\n")
    rc = main(["--case-sensitive"])
    assert rc == 0


def test_main_case_sensitive_flag_keeps_case_variants_distinct(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "Apple apple APPLE\n")
    main(["--case-sensitive"])
    out = capsys.readouterr().out
    assert "Apple" in out and "apple" in out and "APPLE" in out


def test_main_top_flag_limits_output_rows(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "a a a b b c d e f\n")
    main(["--top", "1"])
    out = capsys.readouterr().out
    rows = [line for line in out.splitlines() if line.strip()]
    assert len(rows) == 1


def test_main_top_flag_keeps_most_frequent_word(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "a a a b b c d e f\n")
    main(["--top", "1"])
    out = capsys.readouterr().out
    assert "a" in out and "b" not in out


def test_main_min_len_flag_excludes_short_words(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "an apple is tasty\n")
    main(["--min-len", "4"])
    out = capsys.readouterr().out
    words = [line.split("\t")[0] for line in out.splitlines() if line.strip()]
    assert all(len(w) >= 4 for w in words)


def test_main_min_len_flag_returns_zero(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "an apple is tasty\n")
    rc = main(["--min-len", "4"])
    assert rc == 0


def test_main_combined_flags_json_output_ends_with_final_newline(monkeypatch, capsys):
    _feed_stdin(monkeypatch, "Apple apple APPLE banana\n")
    rc = main(["--json", "--case-sensitive", "--top", "2", "--min-len", "3"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.endswith("\n")
