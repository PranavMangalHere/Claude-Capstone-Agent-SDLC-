"""CLI entry point for CSV Summary Report Generator."""
from __future__ import annotations

import csv
import logging
import sys
from typing import List

from csv_summary import accumulator as acc_module
from csv_summary import null_detection
from csv_summary import reader
from csv_summary import reporter
from csv_summary.accumulator import ColumnAccumulator, ColumnResult

logger = logging.getLogger(__name__)


def _process_file(path: str) -> tuple[int, List[ColumnResult]]:
    """Open and process a CSV file, returning row count and column results.

    Tries UTF-8 first; on UnicodeDecodeError retries with Latin-1.

    Args:
        path: Filesystem path to the CSV file.

    Returns:
        Tuple of (total_data_rows, list_of_ColumnResult).
    """
    try:
        with reader.open_with_encoding(path, encoding="utf-8") as file:
            return _run_pass(file)
    except UnicodeDecodeError:
        logger.warning("UTF-8 decode failed for %s; retrying with latin-1", path)
        with reader.open_with_encoding(path, encoding="latin-1") as file:
            return _run_pass(file)


def _run_pass(file) -> tuple[int, List[ColumnResult]]:
    """Perform a single streaming pass over an open CSV file.

    Args:
        file: An open text IO object.

    Returns:
        Tuple of (total_data_rows, list_of_ColumnResult).
    """
    rows = reader.stream_rows(file)

    header = next(rows, None)
    if header is None:
        return -1, []

    accumulators: List[ColumnAccumulator] = [
        ColumnAccumulator(col_name) for col_name in header
    ]

    total_rows = 0
    for row in rows:
        total_rows += 1
        for idx, cell in enumerate(row):
            if idx < len(accumulators):
                is_null_flag = null_detection.is_null(cell)
                accumulators[idx].update(cell, is_null_flag)

    return total_rows, [a.finalize() for a in accumulators]


def main() -> None:
    """Run the CSV summary pipeline.

    Reads the file at sys.argv[1], computes per-column statistics,
    and prints the summary report to stdout. Exits with code 1 on error.
    """
    if len(sys.argv) < 2:
        print("Usage: python -m csv_summary <path-to-csv>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]

    try:
        total_rows, results = _process_file(path)

        if total_rows == -1 or total_rows == 0 and not results:
            print("No data rows found.")
            return

        if total_rows == 0:
            print("No data rows found.")
            return

        reporter.print_report(total_rows, results)

    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Permission denied: {e}", file=sys.stderr)
        sys.exit(1)
    except csv.Error as e:
        print(f"CSV error: {e}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"Encoding error (tried utf-8 and latin-1): {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error ({type(e).__name__}): {e}", file=sys.stderr)
        sys.exit(1)
