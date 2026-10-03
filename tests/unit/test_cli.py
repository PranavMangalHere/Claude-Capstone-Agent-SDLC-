"""Unit tests for cli.main()."""
from __future__ import annotations

import pathlib
import sys
from unittest import mock

import pytest

from csv_summary import cli


def run_main(argv: list[str], capsys) -> int:
    """Patch sys.argv, run main(), capture exit code via SystemExit."""
    with mock.patch("sys.argv", argv):
        try:
            cli.main()
            return 0
        except SystemExit as e:
            return int(e.code) if e.code is not None else 0


class TestZeroArgumentInvocation:
    """No argument → stderr usage message and exit code 1."""

    def test_zero_args_exits_with_code_1(self, capsys) -> None:
        exit_code = run_main(["csv_summary"], capsys)
        assert exit_code == 1

    def test_zero_args_prints_usage_to_stderr(self, capsys) -> None:
        run_main(["csv_summary"], capsys)
        captured = capsys.readouterr()
        assert len(captured.err) > 0


class TestValidFileInvocation:
    """Valid CSV file → exit code 0."""

    def test_valid_file_exits_with_code_0(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
        exit_code = run_main(["csv_summary", str(csv_file)], capsys)
        assert exit_code == 0


class TestFileNotFoundError:
    """Non-existent file → stderr message and exit code 1."""

    def test_missing_file_exits_with_code_1(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        missing = tmp_path / "ghost.csv"
        exit_code = run_main(["csv_summary", str(missing)], capsys)
        assert exit_code == 1

    def test_missing_file_prints_to_stderr(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        missing = tmp_path / "ghost.csv"
        run_main(["csv_summary", str(missing)], capsys)
        captured = capsys.readouterr()
        assert len(captured.err) > 0

    def test_missing_file_nothing_to_stdout(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        missing = tmp_path / "ghost.csv"
        run_main(["csv_summary", str(missing)], capsys)
        captured = capsys.readouterr()
        assert captured.out == ""


class TestPermissionError:
    """Permission denied → stderr message and exit code 1."""

    def test_permission_error_exits_with_code_1(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "locked.csv"
        csv_file.write_text("a,b\n1,2\n", encoding="utf-8")
        with mock.patch(
            "csv_summary.reader.open_with_encoding",
            side_effect=PermissionError("access denied"),
        ):
            exit_code = run_main(["csv_summary", str(csv_file)], capsys)
        assert exit_code == 1

    def test_permission_error_prints_to_stderr(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "locked.csv"
        csv_file.write_text("a,b\n1,2\n", encoding="utf-8")
        with mock.patch(
            "csv_summary.reader.open_with_encoding",
            side_effect=PermissionError("access denied"),
        ):
            run_main(["csv_summary", str(csv_file)], capsys)
        captured = capsys.readouterr()
        assert len(captured.err) > 0


class TestHeaderOnlyFile:
    """Header-only file → 'No data rows found.' and exit code 0."""

    def test_header_only_exits_with_code_0(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("col1,col2\n", encoding="utf-8")
        exit_code = run_main(["csv_summary", str(csv_file)], capsys)
        assert exit_code == 0

    def test_header_only_prints_no_data_rows_found(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("col1,col2\n", encoding="utf-8")
        run_main(["csv_summary", str(csv_file)], capsys)
        captured = capsys.readouterr()
        assert "No data rows found." in captured.out


class TestZeroByteFile:
    """Empty (0-byte) file → 'No data rows found.' and exit code 0."""

    def test_empty_file_exits_with_code_0(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "empty.csv"
        csv_file.write_bytes(b"")
        exit_code = run_main(["csv_summary", str(csv_file)], capsys)
        assert exit_code == 0

    def test_empty_file_prints_no_data_rows_found(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "empty.csv"
        csv_file.write_bytes(b"")
        run_main(["csv_summary", str(csv_file)], capsys)
        captured = capsys.readouterr()
        assert "No data rows found." in captured.out


class TestCatchAllUnexpectedError:
    """Unexpected exceptions include class name and message in stderr."""

    def test_unexpected_error_exits_with_code_1(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b\n1,2\n", encoding="utf-8")
        with mock.patch(
            "csv_summary.reporter.print_report",
            side_effect=RuntimeError("something went wrong"),
        ):
            exit_code = run_main(["csv_summary", str(csv_file)], capsys)
        assert exit_code == 1

    def test_unexpected_error_includes_exception_class_name_in_stderr(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b\n1,2\n", encoding="utf-8")
        with mock.patch(
            "csv_summary.reporter.print_report",
            side_effect=RuntimeError("something went wrong"),
        ):
            run_main(["csv_summary", str(csv_file)], capsys)
        captured = capsys.readouterr()
        assert "RuntimeError" in captured.err

    def test_unexpected_error_includes_message_in_stderr(
        self, tmp_path: pathlib.Path, capsys
    ) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b\n1,2\n", encoding="utf-8")
        with mock.patch(
            "csv_summary.reporter.print_report",
            side_effect=RuntimeError("something went wrong"),
        ):
            run_main(["csv_summary", str(csv_file)], capsys)
        captured = capsys.readouterr()
        assert "something went wrong" in captured.err
