"""Unit tests for null_detection.is_null()."""
from __future__ import annotations

import pytest

from csv_summary.null_detection import is_null


class TestNullSentinelsExactCase:
    """All six sentinel literals in their default lowercase form."""

    def test_empty_string_is_null(self) -> None:
        assert is_null("") is True

    def test_null_sentinel_is_null(self) -> None:
        assert is_null("null") is True

    def test_n_a_sentinel_is_null(self) -> None:
        assert is_null("n/a") is True

    def test_na_sentinel_is_null(self) -> None:
        assert is_null("na") is True

    def test_nan_sentinel_is_null(self) -> None:
        assert is_null("nan") is True

    def test_none_sentinel_is_null(self) -> None:
        assert is_null("none") is True


class TestNullSentinelsCaseInsensitive:
    """Upper and mixed case variants of null sentinels."""

    def test_uppercase_NULL_is_null(self) -> None:
        assert is_null("NULL") is True

    def test_uppercase_N_A_is_null(self) -> None:
        assert is_null("N/A") is True

    def test_mixed_case_NaN_is_null(self) -> None:
        assert is_null("NaN") is True

    def test_mixed_case_None_is_null(self) -> None:
        assert is_null("None") is True

    def test_uppercase_NA_is_null(self) -> None:
        assert is_null("NA") is True

    def test_uppercase_NAN_is_null(self) -> None:
        assert is_null("NAN") is True


class TestNullWhitespace:
    """Whitespace-only strings should be treated as null after stripping."""

    def test_whitespace_only_is_null(self) -> None:
        assert is_null("   ") is True

    def test_tabs_only_is_null(self) -> None:
        assert is_null("\t") is True

    def test_null_with_surrounding_spaces_is_null(self) -> None:
        assert is_null("  null  ") is True


class TestNonNullValues:
    """Actual values should not be treated as null."""

    def test_hello_is_not_null(self) -> None:
        assert is_null("hello") is False

    def test_numeric_string_is_not_null(self) -> None:
        assert is_null("123") is False

    def test_date_string_is_not_null(self) -> None:
        assert is_null("2023-01-01") is False

    def test_zero_string_is_not_null(self) -> None:
        assert is_null("0") is False

    def test_false_string_is_not_null(self) -> None:
        assert is_null("false") is False
