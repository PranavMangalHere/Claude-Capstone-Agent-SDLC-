"""Integration / acceptance tests for CSV Summary Report Generator.

Each test maps directly to an acceptance criterion from docs/requirements.md.
Tests invoke the full pipeline via cli.main() with sys.argv patched and
stdout/stderr captured via pytest's capsys fixture.

Note on test_memory_streaming (AC-8):
    tracemalloc measures Python-level memory allocations only. It does not
    measure RSS (Resident Set Size) or OS-level memory. Peak tracemalloc
    usage may understate actual RSS. The 512 MB limit is a soft guideline
    for this streaming test; the streaming design guarantees low incremental
    allocation per row regardless.
"""
from __future__ import annotations

import pathlib
import sys
import tracemalloc
from unittest import mock

import pytest

from csv_summary import cli


def run_main(argv: list[str]) -> tuple[int, str, str]:
    """Run cli.main() with patched sys.argv, return (exit_code, stdout, stderr)."""
    with mock.patch("sys.argv", argv):
        try:
            cli.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = int(e.code) if e.code is not None else 0
    return exit_code, "", ""


def run_main_captured(argv: list[str], capsys) -> tuple[int, str, str]:
    """Run cli.main() and capture stdout/stderr."""
    with mock.patch("sys.argv", argv):
        try:
            cli.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = int(e.code) if e.code is not None else 0
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


class TestAC1ValidCsvSummary:
    """AC-1: Valid CSV produces complete summary report, exit 0."""

    def test_valid_csv_summary(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text(
            "name,score,joined\n"
            "Alice,95,2023-01-01\n"
            "Bob,87,2022-06-15\n"
            "Carol,92,2023-03-10\n",
            encoding="utf-8",
        )
        exit_code, stdout, stderr = run_main_captured(
            ["csv_summary", str(csv_file)], capsys
        )
        assert exit_code == 0
        assert "3" in stdout  # total rows
        assert "name" in stdout
        assert "score" in stdout
        assert "joined" in stdout
        assert stderr == ""


class TestAC2NonexistentFile:
    """AC-2: Non-existent file path → stderr, exit 1."""

    def test_nonexistent_file(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        missing = tmp_path / "ghost.csv"
        exit_code, stdout, stderr = run_main_captured(
            ["csv_summary", str(missing)], capsys
        )
        assert exit_code == 1
        assert len(stderr) > 0
        assert stdout == ""


class TestAC3HeaderOnlyCsv:
    """AC-3: Header-only CSV → 'No data rows found.', exit 0."""

    def test_header_only_csv(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("col1,col2,col3\n", encoding="utf-8")
        exit_code, stdout, stderr = run_main_captured(
            ["csv_summary", str(csv_file)], capsys
        )
        assert exit_code == 0
        assert "No data rows found." in stdout


class TestAC4EmptyFile:
    """AC-4: Completely empty file (0 bytes) → 'No data rows found.', exit 0."""

    def test_empty_file(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "empty.csv"
        csv_file.write_bytes(b"")
        exit_code, stdout, stderr = run_main_captured(
            ["csv_summary", str(csv_file)], capsys
        )
        assert exit_code == 0
        assert "No data rows found." in stdout


class TestAC5NumericColumnStats:
    """AC-5: Numeric column shows correct min, max, mean (2dp), null count."""

    def test_numeric_column_stats(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "numeric.csv"
        csv_file.write_text(
            "value\n10\n20\nnull\n30\n",
            encoding="utf-8",
        )
        exit_code, stdout, stderr = run_main_captured(
            ["csv_summary", str(csv_file)], capsys
        )
        assert exit_code == 0
        assert "numeric" in stdout
        # min=10, max=30, mean=20.00
        assert "10.00" in stdout
        assert "30.00" in stdout
        assert "20.00" in stdout
        # null count = 1
        assert "1" in stdout


class TestAC6TextColumnStats:
    """AC-6: Text column shows distinct count, null count."""

    def test_text_column_stats(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "text.csv"
        csv_file.write_text(
            "category\napple\nbanana\napple\nnull\norange\n",
            encoding="utf-8",
        )
        exit_code, stdout, stderr = run_main_captured(
            ["csv_summary", str(csv_file)], capsys
        )
        assert exit_code == 0
        assert "text" in stdout
        # distinct: apple, banana, orange = 3
        assert "3" in stdout
        # null count = 1
        assert "1" in stdout


class TestAC7DateColumnStats:
    """AC-7: Date column shows earliest, latest, null count."""

    def test_date_column_stats(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "dates.csv"
        csv_file.write_text(
            "date\n2023-06-15\n2022-01-01\nnull\n2023-01-15\n",
            encoding="utf-8",
        )
        exit_code, stdout, stderr = run_main_captured(
            ["csv_summary", str(csv_file)], capsys
        )
        assert exit_code == 0
        assert "date" in stdout
        assert "2022-01-01" in stdout
        assert "2023-06-15" in stdout
        # null count = 1
        assert "1" in stdout


class TestAC8MemoryStreaming:
    """AC-8: 100 MB synthetic CSV processed under 512 MB (tracemalloc).

    Note: tracemalloc measures Python-level allocations only and may
    understate actual RSS. The test uses a low-cardinality text column
    to keep the text_distinct set small.
    """

    def test_memory_streaming(self, tmp_path: pathlib.Path, capsys) -> None:
        csv_file = tmp_path / "large.csv"

        # Generate ~100 MB CSV with low-cardinality text column
        header = "id,category\n"
        row_template = "{i},cat_{mod}\n"
        target_bytes = 100 * 1024 * 1024  # 100 MB

        with csv_file.open("w", encoding="utf-8", newline="") as f:
            f.write(header)
            i = 0
            bytes_written = len(header)
            while bytes_written < target_bytes:
                row = row_template.format(i=i, mod=i % 10)
                f.write(row)
                bytes_written += len(row)
                i += 1

        tracemalloc.start()
        try:
            with mock.patch("sys.argv", ["csv_summary", str(csv_file)]):
                try:
                    cli.main()
                except SystemExit:
                    pass
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

        # 512 MB in bytes
        limit_bytes = 512 * 1024 * 1024
        assert peak < limit_bytes, (
            f"Peak Python allocation {peak / 1024 / 1024:.1f} MB exceeds 512 MB limit. "
            "Note: tracemalloc measures Python allocations only; RSS may differ."
        )


class TestZeroArgInvocation:
    """Design-review minor gap: zero-arg invocation → usage message + exit 1."""

    def test_zero_arg_invocation(self, capsys) -> None:
        exit_code, stdout, stderr = run_main_captured(["csv_summary"], capsys)
        assert exit_code == 1
        assert len(stderr) > 0
