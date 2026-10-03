"""Column accumulator for single-pass streaming statistics."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_ISO_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?$')


@dataclass
class ColumnResult:
    """Finalised statistics for a single CSV column."""

    name: str
    col_type: str
    null_count: int
    total_count: int
    num_min: Optional[float] = None
    num_max: Optional[float] = None
    num_mean: Optional[float] = None
    date_min: Optional[str] = None
    date_max: Optional[str] = None
    text_distinct_count: Optional[int] = None


class ColumnAccumulator:
    """Accumulates per-column statistics in a single streaming pass.

    Memory design note:
        text_distinct is only populated once both is_all_numeric and
        is_all_date have been cleared (i.e., the column is confirmed text).
        This prevents memory explosion for high-cardinality numeric or date
        columns, while maintaining accurate distinct counts for text columns.
        For a column that transitions from numeric/date to text mid-stream,
        distinct count will only include values seen after the transition.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.null_count: int = 0
        self.total_count: int = 0
        self.is_all_date: bool = True
        self.is_all_numeric: bool = True
        self.num_min: Optional[float] = None
        self.num_max: Optional[float] = None
        self.num_sum: float = 0.0
        self.num_count: int = 0
        self.date_min: Optional[str] = None
        self.date_max: Optional[str] = None
        self.date_count: int = 0
        self.text_distinct: set[str] = set()

    def _try_parse_date(self, value: str) -> bool:
        """Return True if value matches ISO 8601 date/datetime format."""
        if not _ISO_DATE_RE.match(value):
            return False
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False

    def _try_parse_numeric(self, value: str) -> Optional[float]:
        """Return float if value is numeric, else None."""
        try:
            return float(value)
        except ValueError:
            return None

    def update(self, value: str, is_null: bool) -> None:
        """Update accumulators for one cell value.

        Args:
            value: The raw cell string.
            is_null: Whether the cell has been determined to be null.
        """
        self.total_count += 1
        if is_null:
            self.null_count += 1
            return

        if self.is_all_date:
            if self._try_parse_date(value):
                self.date_count += 1
                self.date_min = (
                    value if self.date_min is None else min(self.date_min, value)
                )
                self.date_max = (
                    value if self.date_max is None else max(self.date_max, value)
                )
            else:
                self.is_all_date = False

        if self.is_all_numeric:
            num = self._try_parse_numeric(value)
            if num is not None:
                self.num_count += 1
                self.num_sum += num
                self.num_min = (
                    num if self.num_min is None else min(self.num_min, num)
                )
                self.num_max = (
                    num if self.num_max is None else max(self.num_max, num)
                )
            else:
                self.is_all_numeric = False

        # Only track distinct values once the column is confirmed text
        # (both numeric and date classification have been ruled out).
        # This prevents O(n) memory usage for high-cardinality numeric columns.
        if not self.is_all_numeric and not self.is_all_date:
            self.text_distinct.add(value)

    def finalize(self) -> ColumnResult:
        """Apply type inference and return a populated ColumnResult."""
        if self.total_count == self.null_count:
            return ColumnResult(
                name=self.name,
                col_type="text",
                null_count=self.null_count,
                total_count=self.total_count,
                text_distinct_count=0,
            )

        if self.is_all_date and self.date_count > 0:
            return ColumnResult(
                name=self.name,
                col_type="date",
                null_count=self.null_count,
                total_count=self.total_count,
                date_min=self.date_min,
                date_max=self.date_max,
            )

        if self.is_all_numeric and self.num_count > 0:
            mean_val = round(self.num_sum / self.num_count, 2)
            return ColumnResult(
                name=self.name,
                col_type="numeric",
                null_count=self.null_count,
                total_count=self.total_count,
                num_min=self.num_min,
                num_max=self.num_max,
                num_mean=mean_val,
            )

        return ColumnResult(
            name=self.name,
            col_type="text",
            null_count=self.null_count,
            total_count=self.total_count,
            text_distinct_count=len(self.text_distinct),
        )
