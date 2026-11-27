# AC#3: return 2 with non-empty stderr on invalid arguments or missing files.
#
# Subtask: main-error-exit-codes
# Target:  wordfreq/cli.py::main

import pytest

from wordfreq.cli import main


@pytest.fixture
def sample_file(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("the quick brown fox jumps over the lazy dog\n", encoding="utf-8")
    return path


@pytest.fixture
def missing_file(tmp_path):
    return tmp_path / "does_not_exist.txt"


INVALID_TOP_CASES = [
    (["--top", "abc"], "top_non_numeric"),
    (["--top", "1.5"], "top_fractional"),
]

INVALID_MIN_LEN_CASES = [
    (["--min-len", "abc"], "min_len_non_numeric"),
    (["--min-len", "1.5"], "min_len_fractional"),
]

UNKNOWN_FLAG_CASES = [
    (["--no-such-flag"], "unknown_long_flag"),
    (["--zzz"], "unknown_short_style_flag"),
]


@pytest.mark.parametrize(
    "flags,case",
    INVALID_TOP_CASES,
    ids=[case for _, case in INVALID_TOP_CASES],
)
def test_main_invalid_top_returns_2(flags, case, sample_file):
    assert main(flags + [str(sample_file)]) == 2


@pytest.mark.parametrize(
    "flags,case",
    INVALID_TOP_CASES,
    ids=[case for _, case in INVALID_TOP_CASES],
)
def test_main_invalid_top_writes_nonempty_stderr(flags, case, sample_file, capsys):
    main(flags + [str(sample_file)])
    assert capsys.readouterr().err != ""


@pytest.mark.parametrize(
    "flags,case",
    INVALID_MIN_LEN_CASES,
    ids=[case for _, case in INVALID_MIN_LEN_CASES],
)
def test_main_invalid_min_len_returns_2(flags, case, sample_file):
    assert main(flags + [str(sample_file)]) == 2


@pytest.mark.parametrize(
    "flags,case",
    INVALID_MIN_LEN_CASES,
    ids=[case for _, case in INVALID_MIN_LEN_CASES],
)
def test_main_invalid_min_len_writes_nonempty_stderr(flags, case, sample_file, capsys):
    main(flags + [str(sample_file)])
    assert capsys.readouterr().err != ""


@pytest.mark.parametrize(
    "flags,case",
    UNKNOWN_FLAG_CASES,
    ids=[case for _, case in UNKNOWN_FLAG_CASES],
)
def test_main_unknown_flag_returns_2(flags, case, sample_file):
    assert main(flags + [str(sample_file)]) == 2


@pytest.mark.parametrize(
    "flags,case",
    UNKNOWN_FLAG_CASES,
    ids=[case for _, case in UNKNOWN_FLAG_CASES],
)
def test_main_unknown_flag_writes_nonempty_stderr(flags, case, sample_file, capsys):
    main(flags + [str(sample_file)])
    assert capsys.readouterr().err != ""


def test_main_missing_file_returns_2(missing_file):
    assert main([str(missing_file)]) == 2


def test_main_missing_file_writes_nonempty_stderr(missing_file, capsys):
    main([str(missing_file)])
    assert capsys.readouterr().err != ""
