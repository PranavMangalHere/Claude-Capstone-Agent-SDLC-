"""Smoke tests for the python -m csv_summary entry point."""
from __future__ import annotations

import pathlib
import subprocess
import sys


def test_no_args_exits_with_code_1() -> None:
    """python -m csv_summary with no args must exit with code 1."""
    result = subprocess.run(
        [sys.executable, "-m", "csv_summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_no_args_stderr_is_non_empty() -> None:
    """python -m csv_summary with no args must produce stderr output."""
    result = subprocess.run(
        [sys.executable, "-m", "csv_summary"],
        capture_output=True,
        text=True,
    )
    assert len(result.stderr.strip()) > 0


def test_valid_csv_exits_with_code_0(tmp_path: pathlib.Path) -> None:
    """python -m csv_summary <valid_csv> must exit with code 0."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,value\nAlice,10\nBob,20\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "csv_summary", str(csv_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_valid_csv_stdout_is_non_empty(tmp_path: pathlib.Path) -> None:
    """python -m csv_summary <valid_csv> must produce stdout output."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,value\nAlice,10\nBob,20\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "csv_summary", str(csv_file)],
        capture_output=True,
        text=True,
    )
    assert len(result.stdout.strip()) > 0
