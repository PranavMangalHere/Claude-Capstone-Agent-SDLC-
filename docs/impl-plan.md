# Implementation Plan

**Project:** CSV Summary Report Generator  
**Author:** Implementation Planner Agent  
**Date:** 2026-10-02  
**Based on:** `docs/architecture.md`, `docs/design-review.md`, `docs/requirements.md`

---

## Design Review Resolutions Applied

The following required changes from `docs/design-review.md` are reflected throughout this plan:

- **RC-1:** `open_with_encoding(path: str) -> TextIO` returns a file object opened with `newline=''`; `stream_rows(file: TextIO) -> Iterator[list[str]]` accepts a `TextIO` argument (not a path). `cli.py` owns the `with` block and passes the open file to `stream_rows`. On `UnicodeDecodeError`, `cli.py` re-opens the file with Latin-1 and restarts the pass from byte 0.
- **RC-2:** `ColumnAccumulator.update()` signature is `update(value: str, is_null: bool) -> None`. The caller (`cli.py`) passes the result of `null_detection.is_null(cell)` as the second argument.
- **RC-3:** All `open()` calls in `reader.py` must include `newline=''` per the Python `csv` module documentation, ensuring correct cross-platform handling of embedded newlines.

---

## Task List

| ID | Task Name | Description | Depends On | Complexity | File(s) Affected |
|---|---|---|---|---|---|
| T-01 | Project Scaffolding | Create the package skeleton: `src/csv_summary/__init__.py` (with version string), `pyproject.toml` (stdlib-only, Python 3.9+), `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`, and `tests/conftest.py` with shared fixtures (temp CSV factory helper). No logic; just structure. | None | S | `src/csv_summary/__init__.py`, `pyproject.toml`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`, `tests/conftest.py` |
| T-02 | null_detection module | Implement `is_null(value: str) -> bool` in `null_detection.py`. Strips the value, lower-cases it, and checks membership against the sentinel set `{"", "null", "n/a", "na", "nan", "none"}`. No other logic. | T-01 | S | `src/csv_summary/null_detection.py` |
| T-02-TEST | Test: null_detection module | Unit tests for `is_null()`: all six sentinel literals (exact case), all sentinel variants in upper/mixed/lower case, whitespace-only string, non-null values (numeric string, date string, plain word). Must achieve full branch coverage of `is_null`. | T-02 | S | `tests/unit/test_null_detection.py` |
| T-03 | accumulator module | Implement `ColumnResult` dataclass and `ColumnAccumulator` class. `ColumnResult` fields: `name: str`, `col_type: str`, `null_count: int`, `total_count: int`, and type-specific optional fields (`num_min`, `num_max`, `num_mean`, `date_min`, `date_max`, `text_distinct_count`). `ColumnAccumulator.__init__(name: str)` initialises all state counters and flags per architecture spec. `update(value: str, is_null: bool) -> None` updates null/total counts; if not null, attempts ISO 8601 date match (regex pre-check then `datetime.fromisoformat`) and numeric parse (`float()`), clears `is_all_date`/`is_all_numeric` flags on first failure. `finalize() -> ColumnResult` applies type inference logic (all-null → text; date priority; numeric; text fallback) and returns a populated `ColumnResult`. RC-2 interface is enforced: `update` always receives both `value` and `is_null`. | T-01 | M | `src/csv_summary/accumulator.py` |
| T-03-TEST | Test: accumulator module | Unit tests for `ColumnAccumulator`: numeric type inference with correct min/max/mean (2 dp); date type inference with ISO 8601 `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SS`; text fallback on mixed values; all-null column → text with `unique_count=0`; single-row column; null_count correctness; `date_min`/`date_max` lexicographic ordering; `text_distinct_count` with duplicate values; rounding of mean to 2 decimal places. All tests call `update(value, is_null)` per RC-2. | T-03 | M | `tests/unit/test_accumulator.py` |
| T-04 | reader module | Implement `open_with_encoding(path: str) -> TextIO` and `stream_rows(file: TextIO) -> Iterator[list[str]]` per RC-1 and RC-3. `open_with_encoding` opens the file with UTF-8 and `newline=''`; if the caller catches `UnicodeDecodeError` during reading, it should re-call with a Latin-1 TextIO (the caller is `cli.py`). `stream_rows(file: TextIO)` wraps `csv.reader(file)` and `yield`s each row as `list[str]`. All `open()` calls must specify `newline=''` (RC-3). `open_with_encoding` does not read any bytes itself; it only opens and returns the file object. | T-01 | S | `src/csv_summary/reader.py` |
| T-04-TEST | Test: reader module | Unit tests for `reader.py`: `open_with_encoding` returns a readable `TextIO` for an existing UTF-8 file; `stream_rows` yields correct rows from a UTF-8 file with quoted commas; `stream_rows` on a 0-byte file yields zero rows; `stream_rows` on a header-only file yields exactly one row; Latin-1 file read via Latin-1-encoded `TextIO` returns correct text; `FileNotFoundError` raised by `open_with_encoding` for a missing path. Verify `newline=''` is respected (no `\r\n` corruption on synthetic Windows-line-ending content). | T-04 | S | `tests/unit/test_reader.py` |
| T-05 | reporter module | Implement `print_report(total_rows: int, results: list[ColumnResult]) -> None` in `reporter.py`. Formats and writes to `sys.stdout`: a total-row-count line, then for each `ColumnResult` a column header line with its inferred type and type-specific statistics (numeric: min/max/mean/nulls; date: earliest/latest/nulls; text: distinct/nulls). No logic — formatting and printing only. Output must be plain text, human-readable (NFR-6). Values displayed exactly as stored for dates (OQ-1 resolution). | T-03 | S | `src/csv_summary/reporter.py` |
| T-05-TEST | Test: reporter module | Unit tests for `print_report()` capturing stdout via `io.StringIO` or `capsys`: numeric column section contains correct labels and rounded values; date column section shows earliest/latest as stored strings; text column section shows distinct and null counts; total row count line present; multiple columns all appear in output; empty `results` list outputs only the total row count line. | T-05 | S | `tests/unit/test_reporter.py` |
| T-06 | cli module | Implement `cli.main() -> None` in `cli.py`. Parses `sys.argv`; exits with code 1 + usage message to stderr if no argument supplied (design-review minor gap). Calls `reader.open_with_encoding(path)` in a `with` block; passes the `TextIO` to `reader.stream_rows(file)` per RC-1; catches `UnicodeDecodeError` mid-stream, closes the file, re-opens with Latin-1 + `newline=''`, and re-runs the full pass. Reads first yielded row as header; instantiates one `ColumnAccumulator` per column. For each data row calls `null_detection.is_null(cell)` then `accumulator.update(cell, is_null_flag)` per RC-2. After exhausting the iterator, calls `finalize()` on each accumulator and passes results to `reporter.print_report()`. Handles `FileNotFoundError`, `PermissionError`, `csv.Error`, `UnicodeDecodeError` (both-encodings failure), and catch-all `Exception` — all with message `f"Unexpected error ({type(e).__name__}): {e}"` to stderr and `sys.exit(1)`. Prints `"No data rows found."` to stdout and exits 0 for empty/header-only files. | T-02, T-03, T-04, T-05 | M | `src/csv_summary/cli.py` |
| T-06-TEST | Test: cli module (unit) | Unit tests for `cli.main()` with `sys.argv` patched and `sys.stdout`/`sys.stderr` captured: zero-argument invocation → stderr message + exit 1; two-argument invocation (with valid file) → exit 0; `FileNotFoundError` path → stderr + exit 1; `PermissionError` → stderr + exit 1; header-only file → stdout "No data rows found." + exit 0; zero-byte file → stdout "No data rows found." + exit 0; catch-all unexpected error includes exception class name and message in stderr output. | T-06 | M | `tests/unit/test_cli.py` |
| T-07 | __main__ entry point | Implement `src/csv_summary/__main__.py` with a two-line body: `from .cli import main` and `main()`. This enables `python -m csv_summary` invocation (FR-1). | T-06 | S | `src/csv_summary/__main__.py` |
| T-07-TEST | Test: __main__ entry point | Smoke test: invoke the package as a subprocess with `python -m csv_summary` (no args) and assert the process exits with code 1 and stderr is non-empty. Invoke with a valid temp CSV and assert exit code 0. Confirms the entry point wires to `cli.main()` without import errors. | T-07 | S | `tests/unit/test_main.py` |
| T-08 | Integration / acceptance tests | Implement all AC-mapped integration tests in `tests/integration/test_acceptance.py` using real temporary CSV files (via `tmp_path` fixture). Each test invokes the full pipeline through `cli.main()` with `sys.argv` patched and stdout/stderr captured. Tests: `test_valid_csv_summary` (AC-1), `test_nonexistent_file` (AC-2), `test_header_only_csv` (AC-3), `test_empty_file` (AC-4), `test_numeric_column_stats` (AC-5), `test_text_column_stats` (AC-6), `test_date_column_stats` (AC-7), `test_memory_streaming` (AC-8 — synthetic 100 MB CSV with low-cardinality text column, measured via `tracemalloc`; explicitly document that `tracemalloc` measures Python allocations only and may understate RSS). Also add `test_zero_arg_invocation` (design-review minor gap). | T-07, T-06-TEST | L | `tests/integration/test_acceptance.py` |

---

## Dependency Graph

```
T-01 (Scaffolding)
 ├── T-02 (null_detection)
 │    └── T-02-TEST
 ├── T-03 (accumulator)
 │    └── T-03-TEST
 ├── T-04 (reader)
 │    └── T-04-TEST
 └── (T-03 also needed by T-05)
      └── T-05 (reporter)
           └── T-05-TEST

T-02 ──┐
T-03 ──┤
T-04 ──┼──► T-06 (cli)
T-05 ──┘     ├── T-06-TEST
             └── T-07 (__main__)
                  ├── T-07-TEST
                  └── T-08 (integration tests)
```

**Valid topological execution order:**

T-01 → T-02 → T-02-TEST → T-03 → T-03-TEST → T-04 → T-04-TEST → T-05 → T-05-TEST → T-06 → T-06-TEST → T-07 → T-07-TEST → T-08

---

## Blocked Tasks

| Task ID | Blocked By | Resolution Needed |
|---|---|---|
| — | — | No external blockers. All tasks use stdlib-only components and local filesystem I/O. No API keys, external services, or human decisions are required. |

---

## Requirements Traceability

| Requirement | Covered By Task(s) |
|---|---|
| FR-1 (CLI invocation) | T-07, T-08 |
| FR-2 (read CSV, print report) | T-06, T-08 |
| FR-3 (total data row count) | T-05, T-06 |
| FR-4 (column name + inferred type) | T-03, T-05 |
| FR-5 (numeric stats) | T-03, T-05 |
| FR-6 (text stats) | T-03, T-05 |
| FR-7 (date stats) | T-03, T-05 |
| FR-8 (date classification rule) | T-03 |
| FR-9 (numeric classification rule) | T-03 |
| FR-10 (text fallback rule) | T-03 |
| FR-11 (all-null → text) | T-03 |
| FR-12 (null sentinels) | T-02 |
| FR-13 (file not found → exit 1) | T-06 |
| FR-14 (empty/header-only → exit 0) | T-06 |
| FR-15 (all other errors → exit 1) | T-06 |
| FR-16 (first row is header) | T-06 |
| FR-17 (comma delimiter) | T-04 |
| FR-18 (UTF-8 / Latin-1 fallback) | T-04, T-06 |
| NFR-1 / NFR-2 (streaming, memory bound) | T-04, T-06, T-08 |
| NFR-3 (Python 3.9+) | T-01 (pyproject.toml) |
| NFR-4 (stdlib only) | T-01 through T-08 |
| NFR-5 (portability, newline='') | T-04 (RC-3) |
| NFR-6 (human-readable output) | T-05 |
| NFR-7 (2 dp rounding) | T-03, T-05 |
| NFR-8 (exit codes) | T-06, T-07 |
| AC-1 | T-08 (`test_valid_csv_summary`) |
| AC-2 | T-08 (`test_nonexistent_file`) |
| AC-3 | T-08 (`test_header_only_csv`) |
| AC-4 | T-08 (`test_empty_file`) |
| AC-5 | T-08 (`test_numeric_column_stats`) |
| AC-6 | T-08 (`test_text_column_stats`) |
| AC-7 | T-08 (`test_date_column_stats`) |
| AC-8 | T-08 (`test_memory_streaming`) |

---

## Definition of Done

- [ ] All T-XX tasks implemented and passing their paired T-XX-TEST tasks
- [ ] `pytest tests/` exits with 0 failures
- [ ] All files listed in "File(s) Affected" exist and are non-empty
- [ ] Every functional requirement in `docs/requirements.md` is traceable to at least one task (see traceability table above)
- [ ] `python -m csv_summary` (no args) exits with code 1 and non-empty stderr
- [ ] `python -m csv_summary <valid_csv>` exits with code 0 and non-empty stdout
- [ ] No third-party imports appear in any `src/` file
- [ ] All `open()` calls in `reader.py` include `newline=''`
- [ ] `ColumnAccumulator.update()` signature is `update(value: str, is_null: bool) -> None` throughout
