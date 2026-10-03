"""Shared pytest fixtures for CSV Summary Report Generator tests."""
from __future__ import annotations

import pathlib

import pytest


@pytest.fixture
def tmp_csv(tmp_path: pathlib.Path):
    """Factory fixture that creates a temporary CSV file with given content.

    Returns a callable that accepts content (str) and optional filename (str)
    and writes it to a temp file, returning the Path.
    """

    def _make_csv(content: str, filename: str = "test.csv") -> pathlib.Path:
        csv_file = tmp_path / filename
        csv_file.write_text(content, encoding="utf-8")
        return csv_file

    return _make_csv
