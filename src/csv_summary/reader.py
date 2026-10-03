"""Streaming CSV reader with encoding fallback support."""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import IO, Iterator

logger = logging.getLogger(__name__)


def open_with_encoding(path: str, encoding: str = "utf-8") -> IO[str]:
    """Open a CSV file with the specified encoding and newline='' (RC-3).

    Args:
        path: Filesystem path to the CSV file.
        encoding: Character encoding to use (default: utf-8).

    Returns:
        An open text file object suitable for passing to stream_rows().

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return file_path.open(mode="r", encoding=encoding, newline="")


def stream_rows(file: IO[str]) -> Iterator[list[str]]:
    """Yield each row of a CSV file as a list of string cell values.

    Args:
        file: An open text file object (e.g. from open_with_encoding()).

    Yields:
        Each parsed CSV row as a list of strings.
    """
    reader = csv.reader(file)
    for row in reader:
        yield row
