"""Unit tests for reporter.print_report()."""
from __future__ import annotations

import io
import sys

import pytest

from csv_summary.accumulator import ColumnResult
from csv_summary.reporter import print_report


def capture_report(total_rows: int, results: list) -> str:
    """Helper to capture print_report output as a string."""
    captured = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured
    try:
        print_report(total_rows, results)
    finally:
        sys.stdout = original_stdout
    return captured.getvalue()


class TestTotalRowCountLine:
    """The total row count line must appear in the output."""

    def test_total_row_count_line_present(self) -> None:
        output = capture_report(42, [])
        assert "42" in output

    def test_empty_results_still_shows_total_row_count(self) -> None:
        output = capture_report(0, [])
        assert "0" in output
        assert "Total" in output or "total" in output.lower()


class TestNumericColumnSection:
    """Numeric columns must show min, max, mean, and null count."""

    def _make_numeric(self) -> ColumnResult:
        return ColumnResult(
            name="price",
            col_type="numeric",
            null_count=1,
            total_count=4,
            num_min=1.0,
            num_max=10.0,
            num_mean=5.33,
        )

    def test_numeric_type_label_present(self) -> None:
        output = capture_report(3, [self._make_numeric()])
        assert "numeric" in output

    def test_numeric_column_name_present(self) -> None:
        output = capture_report(3, [self._make_numeric()])
        assert "price" in output

    def test_numeric_min_value_present(self) -> None:
        output = capture_report(3, [self._make_numeric()])
        assert "1.00" in output

    def test_numeric_max_value_present(self) -> None:
        output = capture_report(3, [self._make_numeric()])
        assert "10.00" in output

    def test_numeric_mean_value_present(self) -> None:
        output = capture_report(3, [self._make_numeric()])
        assert "5.33" in output

    def test_numeric_null_count_present(self) -> None:
        output = capture_report(3, [self._make_numeric()])
        assert "1" in output


class TestDateColumnSection:
    """Date columns must show earliest, latest, and null count."""

    def _make_date(self) -> ColumnResult:
        return ColumnResult(
            name="created_at",
            col_type="date",
            null_count=2,
            total_count=5,
            date_min="2022-01-01",
            date_max="2023-12-31",
        )

    def test_date_type_label_present(self) -> None:
        output = capture_report(3, [self._make_date()])
        assert "date" in output

    def test_date_column_name_present(self) -> None:
        output = capture_report(3, [self._make_date()])
        assert "created_at" in output

    def test_date_earliest_present(self) -> None:
        output = capture_report(3, [self._make_date()])
        assert "2022-01-01" in output

    def test_date_latest_present(self) -> None:
        output = capture_report(3, [self._make_date()])
        assert "2023-12-31" in output

    def test_date_null_count_present(self) -> None:
        output = capture_report(3, [self._make_date()])
        assert "2" in output


class TestTextColumnSection:
    """Text columns must show distinct count and null count."""

    def _make_text(self) -> ColumnResult:
        return ColumnResult(
            name="category",
            col_type="text",
            null_count=3,
            total_count=10,
            text_distinct_count=5,
        )

    def test_text_type_label_present(self) -> None:
        output = capture_report(7, [self._make_text()])
        assert "text" in output

    def test_text_column_name_present(self) -> None:
        output = capture_report(7, [self._make_text()])
        assert "category" in output

    def test_text_distinct_count_present(self) -> None:
        output = capture_report(7, [self._make_text()])
        assert "5" in output

    def test_text_null_count_present(self) -> None:
        output = capture_report(7, [self._make_text()])
        assert "3" in output


class TestMultipleColumns:
    """All columns must appear in output."""

    def test_multiple_columns_all_appear(self) -> None:
        results = [
            ColumnResult("col_a", "text", 0, 3, text_distinct_count=2),
            ColumnResult("col_b", "numeric", 1, 3, num_min=1.0, num_max=5.0, num_mean=3.0),
        ]
        output = capture_report(3, results)
        assert "col_a" in output
        assert "col_b" in output
