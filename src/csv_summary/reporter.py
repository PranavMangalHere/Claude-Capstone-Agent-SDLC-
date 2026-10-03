"""Report formatter for CSV summary statistics."""
from __future__ import annotations

import logging
import sys
from typing import List

from csv_summary.accumulator import ColumnResult

logger = logging.getLogger(__name__)


def _print_numeric_section(result: ColumnResult) -> None:
    """Print statistics for a numeric column."""
    print(f"  Type   : numeric")
    print(f"  Min    : {result.num_min:.2f}")
    print(f"  Max    : {result.num_max:.2f}")
    print(f"  Mean   : {result.num_mean:.2f}")
    print(f"  Nulls  : {result.null_count}")


def _print_date_section(result: ColumnResult) -> None:
    """Print statistics for a date column."""
    print(f"  Type     : date")
    print(f"  Earliest : {result.date_min}")
    print(f"  Latest   : {result.date_max}")
    print(f"  Nulls    : {result.null_count}")


def _print_text_section(result: ColumnResult) -> None:
    """Print statistics for a text column."""
    print(f"  Type     : text")
    print(f"  Distinct : {result.text_distinct_count}")
    print(f"  Nulls    : {result.null_count}")


def print_report(total_rows: int, results: List[ColumnResult]) -> None:
    """Write a human-readable summary report to stdout.

    Args:
        total_rows: Total number of data rows (excluding header).
        results: List of finalised ColumnResult objects.
    """
    print(f"Total data rows: {total_rows}")
    for result in results:
        print(f"\nColumn: {result.name}")
        if result.col_type == "numeric":
            _print_numeric_section(result)
        elif result.col_type == "date":
            _print_date_section(result)
        else:
            _print_text_section(result)
