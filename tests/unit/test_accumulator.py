"""Unit tests for ColumnAccumulator and ColumnResult."""
from __future__ import annotations

import pytest

from csv_summary.accumulator import ColumnAccumulator, ColumnResult


def make_accumulator(name: str = "col") -> ColumnAccumulator:
    """Helper to create a fresh ColumnAccumulator."""
    return ColumnAccumulator(name)


class TestNumericTypeInference:
    """Tests for columns where all values are numeric."""

    def test_numeric_type_is_inferred_correctly(self) -> None:
        acc = make_accumulator("price")
        for v in ["1.0", "2.5", "3.0"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.col_type == "numeric"

    def test_numeric_min_is_correct(self) -> None:
        acc = make_accumulator()
        for v in ["10", "3", "7"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.num_min == 3.0

    def test_numeric_max_is_correct(self) -> None:
        acc = make_accumulator()
        for v in ["10", "3", "7"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.num_max == 10.0

    def test_numeric_mean_is_rounded_to_2dp(self) -> None:
        acc = make_accumulator()
        for v in ["1", "2", "3"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.num_mean == 2.00

    def test_mean_rounding_with_repeating_decimal(self) -> None:
        acc = make_accumulator()
        for v in ["1", "2"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.num_mean == 1.50

    def test_mean_rounded_to_2dp_precision(self) -> None:
        acc = make_accumulator()
        for v in ["1", "2", "4"]:
            acc.update(v, False)
        # sum=7, count=3 → 2.333... rounds to 2.33
        result = acc.finalize()
        assert result.num_mean == 2.33

    def test_numeric_null_count_is_correct(self) -> None:
        acc = make_accumulator()
        acc.update("", True)
        acc.update("5", False)
        acc.update("null", True)
        result = acc.finalize()
        assert result.null_count == 2

    def test_single_numeric_row(self) -> None:
        acc = make_accumulator()
        acc.update("42", False)
        result = acc.finalize()
        assert result.col_type == "numeric"
        assert result.num_min == 42.0
        assert result.num_max == 42.0
        assert result.num_mean == 42.0


class TestDateTypeInference:
    """Tests for columns where all non-null values are ISO 8601 dates."""

    def test_date_type_inferred_for_yyyy_mm_dd(self) -> None:
        acc = make_accumulator("date_col")
        for v in ["2023-01-01", "2023-06-15", "2022-12-31"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.col_type == "date"

    def test_date_type_inferred_for_datetime_format(self) -> None:
        acc = make_accumulator()
        for v in ["2023-01-01T10:00:00", "2023-06-15T23:59:59"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.col_type == "date"

    def test_date_min_is_lexicographic_minimum(self) -> None:
        acc = make_accumulator()
        for v in ["2023-06-15", "2022-01-01", "2023-01-15"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.date_min == "2022-01-01"

    def test_date_max_is_lexicographic_maximum(self) -> None:
        acc = make_accumulator()
        for v in ["2023-06-15", "2022-01-01", "2023-01-15"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.date_max == "2023-06-15"

    def test_date_null_count(self) -> None:
        acc = make_accumulator()
        acc.update("", True)
        acc.update("2023-01-01", False)
        result = acc.finalize()
        assert result.null_count == 1

    def test_date_with_nulls_still_classified_as_date(self) -> None:
        acc = make_accumulator()
        acc.update("", True)
        acc.update("2023-01-01", False)
        result = acc.finalize()
        assert result.col_type == "date"


class TestTextTypeInference:
    """Tests for text fallback and mixed value columns."""

    def test_mixed_values_classified_as_text(self) -> None:
        acc = make_accumulator()
        acc.update("hello", False)
        acc.update("42", False)
        result = acc.finalize()
        assert result.col_type == "text"

    def test_pure_text_values_classified_as_text(self) -> None:
        acc = make_accumulator()
        for v in ["apple", "banana", "cherry"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.col_type == "text"

    def test_text_distinct_count_is_correct(self) -> None:
        acc = make_accumulator()
        for v in ["apple", "banana", "apple", "cherry"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.text_distinct_count == 3

    def test_text_null_count_is_correct(self) -> None:
        acc = make_accumulator()
        acc.update("", True)
        acc.update("hello", False)
        acc.update("none", True)
        result = acc.finalize()
        assert result.null_count == 2

    def test_text_with_duplicate_values(self) -> None:
        acc = make_accumulator()
        for v in ["a", "a", "a"]:
            acc.update(v, False)
        result = acc.finalize()
        assert result.text_distinct_count == 1


class TestAllNullColumn:
    """Tests for columns where every value is null (FR-11)."""

    def test_all_null_column_is_text(self) -> None:
        acc = make_accumulator()
        for v in ["", "null", "N/A"]:
            acc.update(v, True)
        result = acc.finalize()
        assert result.col_type == "text"

    def test_all_null_column_distinct_count_is_zero(self) -> None:
        acc = make_accumulator()
        for _ in range(5):
            acc.update("", True)
        result = acc.finalize()
        assert result.text_distinct_count == 0

    def test_all_null_column_null_count_equals_total(self) -> None:
        acc = make_accumulator()
        for _ in range(3):
            acc.update("null", True)
        result = acc.finalize()
        assert result.null_count == 3
        assert result.total_count == 3


class TestColumnResultFields:
    """Tests for correct ColumnResult field population."""

    def test_column_name_is_preserved(self) -> None:
        acc = ColumnAccumulator("my_column")
        acc.update("1", False)
        result = acc.finalize()
        assert result.name == "my_column"

    def test_total_count_is_correct(self) -> None:
        acc = make_accumulator()
        for v, null in [("1", False), ("", True), ("3", False)]:
            acc.update(v, null)
        result = acc.finalize()
        assert result.total_count == 3
