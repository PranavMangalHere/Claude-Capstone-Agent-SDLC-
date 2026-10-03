"""Unit tests for reader.py — open_with_encoding and stream_rows."""
from __future__ import annotations

import pathlib

import pytest

from csv_summary.reader import open_with_encoding, stream_rows


class TestOpenWithEncoding:
    """Tests for open_with_encoding()."""

    def test_returns_readable_file_for_existing_utf8_file(
        self, tmp_path: pathlib.Path
    ) -> None:
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,2\n", encoding="utf-8")
        with open_with_encoding(str(csv_file)) as f:
            content = f.read()
        assert "a,b" in content

    def test_raises_file_not_found_for_missing_path(
        self, tmp_path: pathlib.Path
    ) -> None:
        missing = tmp_path / "does_not_exist.csv"
        with pytest.raises(FileNotFoundError):
            open_with_encoding(str(missing))

    def test_latin1_file_readable_with_latin1_encoding(
        self, tmp_path: pathlib.Path
    ) -> None:
        csv_file = tmp_path / "latin1.csv"
        # Write a byte sequence valid in Latin-1 but not UTF-8
        csv_file.write_bytes(b"name,value\ncaf\xe9,1\n")
        with open_with_encoding(str(csv_file), encoding="latin-1") as f:
            content = f.read()
        assert "caf\xe9" in content


class TestStreamRows:
    """Tests for stream_rows()."""

    def test_yields_correct_rows_from_utf8_file(
        self, tmp_path: pathlib.Path
    ) -> None:
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")
        with open_with_encoding(str(csv_file)) as f:
            rows = list(stream_rows(f))
        assert rows == [["a", "b", "c"], ["1", "2", "3"], ["4", "5", "6"]]

    def test_handles_quoted_commas_correctly(
        self, tmp_path: pathlib.Path
    ) -> None:
        csv_file = tmp_path / "quoted.csv"
        csv_file.write_text('col1,col2\n"hello, world",42\n', encoding="utf-8")
        with open_with_encoding(str(csv_file)) as f:
            rows = list(stream_rows(f))
        assert rows[1][0] == "hello, world"
        assert rows[1][1] == "42"

    def test_zero_byte_file_yields_no_rows(
        self, tmp_path: pathlib.Path
    ) -> None:
        csv_file = tmp_path / "empty.csv"
        csv_file.write_bytes(b"")
        with open_with_encoding(str(csv_file)) as f:
            rows = list(stream_rows(f))
        assert rows == []

    def test_header_only_file_yields_exactly_one_row(
        self, tmp_path: pathlib.Path
    ) -> None:
        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("col1,col2,col3\n", encoding="utf-8")
        with open_with_encoding(str(csv_file)) as f:
            rows = list(stream_rows(f))
        assert len(rows) == 1
        assert rows[0] == ["col1", "col2", "col3"]

    def test_windows_line_endings_no_carriage_return_corruption(
        self, tmp_path: pathlib.Path
    ) -> None:
        csv_file = tmp_path / "windows.csv"
        # Write Windows-style CRLF line endings as raw bytes
        csv_file.write_bytes(b"col1,col2\r\n1,2\r\n3,4\r\n")
        with open_with_encoding(str(csv_file)) as f:
            rows = list(stream_rows(f))
        # With newline='', csv.reader handles \r\n correctly
        assert rows == [["col1", "col2"], ["1", "2"], ["3", "4"]]
        # No cell should contain a carriage return
        for row in rows:
            for cell in row:
                assert "\r" not in cell
