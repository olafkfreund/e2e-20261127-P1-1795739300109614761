# Criterion (AC#3): main and python -m wordfreq read from sys.stdin by default.
# Subtask: python -m wordfreq reads piped stdin, prints TSV, and exits 2 with
# stderr output for a missing file.

import os
import subprocess
import sys

import pytest

import wordfreq

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(wordfreq.__file__)))


def _run_wordfreq(args, stdin_text=None, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "wordfreq", *args],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=cwd if cwd is not None else _PROJECT_ROOT,
    )


@pytest.fixture
def piped_result():
    return _run_wordfreq([], stdin_text="the cat the dog\n")


def test_python_m_wordfreq_piped_stdin_exits_zero(piped_result):
    assert piped_result.returncode == 0


def test_python_m_wordfreq_piped_stdin_prints_tsv(piped_result):
    lines = [line for line in piped_result.stdout.splitlines() if line.strip()]
    assert lines
    assert all("\t" in line for line in lines)


def test_python_m_wordfreq_missing_file_exits_2(tmp_path):
    missing = tmp_path / "does_not_exist.txt"
    result = _run_wordfreq([str(missing)])
    assert result.returncode == 2


def test_python_m_wordfreq_missing_file_writes_stderr(tmp_path):
    missing = tmp_path / "does_not_exist.txt"
    result = _run_wordfreq([str(missing)])
    assert result.stderr.strip() != ""
