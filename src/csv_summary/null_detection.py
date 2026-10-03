"""Null sentinel detection for CSV cell values."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_NULL_SENTINELS: frozenset[str] = frozenset({"", "null", "n/a", "na", "nan", "none"})


def is_null(value: str) -> bool:
    """Return True if value is a recognised null sentinel (case-insensitive).

    Sentinels: empty string, 'null', 'n/a', 'na', 'nan', 'none'.
    Leading/trailing whitespace is stripped before comparison.
    """
    return value.strip().lower() in _NULL_SENTINELS
