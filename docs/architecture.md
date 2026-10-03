# Architecture

**Project:** CSV Summary Report Generator  
**Author:** Architecture Agent  
**Date:** 2026-10-01  
**Based on:** `docs/requirements.md`

---

## System Overview

The CSV Summary Report Generator is a single-process Python CLI tool that reads one CSV file from disk using streaming I/O, computes per-column descriptive statistics in a single pass, and prints a human-readable summary to stdout. It has no external services, no database, and no third-party dependencies. It is packaged as a standard Python package invocable via `python -m csv_summary <path>` and is compatible with Python 3.9+ on Linux, macOS, and Windows.

---

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        python -m csv_summary                         │
│                                                                      │
│   ┌─────────────┐                                                    │
│   │ __main__.py │  Entry point — delegates to cli.main()            │
│   └──────┬──────┘                                                    │
│          │                                                            │
│   ┌──────▼──────┐   file path    ┌────────────┐                     │
│   │   cli.py    │───────────────►│  reader.py │                     │
│   │ (orchestr.) │◄── row stream ─│ (streaming)│                     │
│   └──────┬──────┘                └────────────┘                     │
│          │                                                            │
│          │  per-cell value                                            │
│          │       ┌──────────────────┐                                │
│          ├──────►│ null_detection.py│                                │
│          │       └──────────────────┘                                │
│          │                                                            │
│          │  (value, is_null) per cell                                 │
│          │       ┌──────────────────┐                                │
│          ├──────►│  accumulator.py  │  (one ColumnAccumulator        │
│          │       │  ColumnAccumul.  │   per column, updated          │
│          │       └──────────────────┘   row-by-row)                 │
│          │                                                            │
│          │  after full file pass                                      │
│          │       ┌──────────────────┐                                │
│          └──────►│  reporter.py     │──► stdout                      │
│                  └──────────────────┘                                │
│                                                                       │
│   ┌────────────────────────────────────────────────────────────┐    │
│   │  Error paths: FileNotFoundError, PermissionError, etc.     │    │
│   │  → descriptive message to stderr, sys.exit(1)              │    │
│   └────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Descriptions

| Component | Responsibility | Key Interfaces |
|---|---|---|
| `__main__.py` | Python package entry point; delegates to `cli.main()` immediately | `python -m csv_summary` invocation |
| `cli.py` | Parses `sys.argv`, validates file path, orchestrates the full pipeline, handles all exceptions, manages exit codes | `main() -> None`; calls `reader`, `null_detection`, `accumulator`, `reporter` |
| `reader.py` | Opens the CSV file with the specified encoding and `newline=''` (RC-3); yields one row at a time via `csv.reader` (streaming, never loads full file); does not handle encoding retry internally — that is `cli.py`'s responsibility | `open_with_encoding(path: str, encoding: str = "utf-8") -> IO[str]`; `stream_rows(file: IO[str]) -> Iterator[list[str]]` |
| `null_detection.py` | Determines whether a single cell value is null per the defined null sentinel set (case-insensitive) | `is_null(value: str) -> bool` |
| `accumulator.py` | Maintains one `ColumnAccumulator` per column; updates per-cell statistics in a single streaming pass; finalizes type inference and stats on demand | `class ColumnAccumulator`; `update(value: str, is_null: bool) -> None`; `finalize() -> ColumnResult` |
| `reporter.py` | Formats and prints the summary report to stdout in a human-readable layout; no logic, only presentation | `print_report(total_rows: int, results: list[ColumnResult]) -> None` |

---

## Module / Package Structure

```
src/
└── csv_summary/
    ├── __init__.py          # Package marker; exports version string
    ├── __main__.py          # Entry point: `from .cli import main; main()`
    ├── cli.py               # Pipeline orchestration, arg parsing, exit codes
    ├── reader.py            # Streaming CSV reader with encoding fallback
    ├── null_detection.py    # Null sentinel detection
    ├── accumulator.py       # ColumnAccumulator, ColumnResult dataclass
    └── reporter.py          # Report formatting and stdout printing

tests/
├── unit/
│   ├── test_null_detection.py    # All null sentinel values, case-insensitivity
│   ├── test_accumulator.py       # Type inference rules, all stat calculations
│   ├── test_reader.py            # Encoding fallback, empty file, header-only
│   └── test_reporter.py          # Output format correctness
└── integration/
    └── test_acceptance.py        # AC-1 through AC-8 using real temp CSV files
```

---

## Data Flow

**Happy path — well-formed CSV with data rows:**

1. The user runs `python -m csv_summary path/to/file.csv`. Python calls `__main__.py`, which calls `cli.main()`.
2. `cli.py` reads `sys.argv[1]` as the file path. If not provided, it prints usage to stderr and exits with code 1.
3. `cli.py` calls `reader.open_with_encoding(path, encoding="utf-8")`, which opens the file with UTF-8 and `newline=''` and returns the file object. If the file does not exist, a `FileNotFoundError` is propagated and caught in `cli.py`, which prints an error to stderr and exits with code 1. The encoding retry (Latin-1 fallback) is managed entirely by `cli.py`: if a `UnicodeDecodeError` is raised during reading, `cli.py` re-calls `reader.open_with_encoding(path, encoding="latin-1")` and restarts the streaming pass from byte 0.
4. `cli.py` calls `reader.stream_rows(file)`, passing the open file object, which wraps `csv.reader` around it. `csv.reader` is lazy: it reads and parses one line at a time from disk, so peak memory is bounded to the current row plus accumulated per-column state — not the entire file.
5. `cli.py` reads the first yielded row as the header row (FR-16) and instantiates one `ColumnAccumulator` per column name.
6. If no header row is yielded (0-byte file) or no data rows follow the header, `cli.py` prints `"No data rows found."` to stdout and exits with code 0 (FR-14).
7. For each subsequent data row yielded by `stream_rows`, `cli.py` iterates over cells. For each cell, it calls `null_detection.is_null(cell)` to determine nullity, then calls `accumulator.update(cell, is_null_flag)` on the corresponding `ColumnAccumulator`.
8. After the iterator is exhausted, `cli.py` calls `accumulator.finalize()` on each `ColumnAccumulator`. `finalize()` applies the type inference rules (date > numeric > text > all-null-text) and returns a `ColumnResult` dataclass containing the inferred type and the pre-computed statistics appropriate to that type.
9. `cli.py` passes `total_data_rows` and the list of `ColumnResult` objects to `reporter.print_report()`.
10. `reporter.print_report()` writes the formatted report to `sys.stdout` and returns.
11. `cli.py` exits with code 0.

**Error paths:**

- File not found: `FileNotFoundError` caught in `cli.py` → message to stderr → `sys.exit(1)`.
- Permission denied: `PermissionError` caught in `cli.py` → message to stderr → `sys.exit(1)`.
- Encoding failure (both UTF-8 and Latin-1 fail): `UnicodeDecodeError` caught in `cli.py` → message to stderr → `sys.exit(1)`.
- Malformed CSV (e.g., `csv.Error`): caught in `cli.py` → message to stderr → `sys.exit(1)`.
- Any other unexpected exception: caught by a top-level `except Exception` in `cli.py` → message including exception class name and string representation (e.g., `f"Unexpected error ({type(e).__name__}): {e}"`) to stderr → `sys.exit(1)`.

---

## ColumnAccumulator Design (Single-Pass Streaming)

Each `ColumnAccumulator` maintains the following state — all O(1) or O(d) where d is distinct text values:

```
null_count:       int = 0
total_count:      int = 0

# Type tracking flags (start optimistic, set False on first disqualifying value)
is_all_date:      bool = True
is_all_numeric:   bool = True

# Numeric accumulators (updated whenever value parses as float)
num_min:          float | None = None
num_max:          float | None = None
num_sum:          float = 0.0
num_count:        int = 0        # non-null numeric count

# Date accumulators (ISO 8601 strings are lexicographically sortable)
date_min:         str | None = None
date_max:         str | None = None
date_count:       int = 0        # non-null date count

# Text accumulator
text_distinct:    set[str] = set()   # non-null values
```

**Type inference logic (applied in `finalize()`):**

```
if total_count == null_count:
    → type = "text", unique_count = 0, null_count = total_count   (FR-11)
elif is_all_date and date_count > 0:
    → type = "date"                                                (FR-8)
elif is_all_numeric and num_count > 0:
    → type = "numeric"                                             (FR-9)
else:
    → type = "text"                                                (FR-10)
```

**Memory note:** For `text_distinct`, the set grows with the number of unique non-null text values in that column. This is necessary to count distinct values accurately. Numeric and date columns consume O(1) memory per column. For a 100 MB file this is well within the 512 MB budget unless a text column has an extremely high cardinality of long strings; in practice, string interning within the set avoids redundant storage.

---

## Technology Choices

| Package / Module | Purpose | Justification |
|---|---|---|
| `csv` (stdlib) | Streaming CSV parsing, handles quoting and escaping correctly | Stdlib; lazy row-by-row iteration satisfies NFR-2; no third-party packages allowed (NFR-4) |
| `sys` (stdlib) | Access to `argv`, `stdout`, `stderr`, `exit()` | Stdlib; required for CLI contract |
| `datetime` (stdlib) | Parsing ISO 8601 date strings for validation and comparison | Stdlib; `datetime.fromisoformat()` available since Python 3.7, covers `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SS` |
| `re` (stdlib) | Pre-validation of ISO 8601 format before `datetime.fromisoformat()` call (to avoid exception-driven flow for non-date values) | Stdlib; regex match is faster than catching exceptions in a tight per-cell loop |
| `dataclasses` (stdlib) | `ColumnResult` typed return value from `finalize()` | Stdlib; clean typed data transfer between accumulator and reporter; available since Python 3.7 |
| `typing` (stdlib) | Type hints throughout for correctness and IDE support, including `IO`, `Iterator`, `List`, `Optional` used in reader and accumulator signatures | Stdlib; compatible with Python 3.9+ |
| `pathlib` (stdlib) | `Path` used in `reader.open_with_encoding()` to check file existence and open the file | Stdlib; cross-platform path handling |

No third-party packages are used anywhere in the implementation (NFR-4).

---

## External Dependencies

| Dependency | Type | Required For | Failure Mode |
|---|---|---|---|
| Input CSV file on local filesystem | File I/O | All processing | File not found → exit 1 (FR-13); permission denied → exit 1 (FR-15); unreadable encoding → exit 1 (FR-15) |
| Python 3.9+ runtime | Runtime | Execution | Tool will not run on older Python; no mitigation in scope |
| Operating system stdout/stderr | Stream I/O | Report output and error messages | OS-level I/O failure is not handled; treated as unrecoverable |

---

## Security Considerations

The tool has a minimal attack surface since it reads only local files specified by the invoking user and writes only to stdout/stderr. Key considerations:

- **Path traversal:** The tool accepts any path the OS allows the running user to read. No sandboxing is implemented, which is consistent with a local CLI tool running under the user's own credentials. No path normalisation or restriction is needed.
- **Malformed input:** Malformed CSV is caught via `csv.Error` and reported cleanly with exit code 1 rather than crashing with a traceback (FR-15). This prevents information leakage via Python tracebacks to unintended consumers.
- **Memory exhaustion (denial-of-service):** Chunk-based streaming (NFR-2) prevents an adversarially large file from loading entirely into RAM. The text distinct-value set is the only unbounded structure; in the worst case it is proportional to the number of unique cells in text columns, which is bounded by total cell count. This is an accepted design trade-off for correct distinct-value counting.
- **Encoding injection:** The Latin-1 fallback encoding is used only to read byte sequences that are not valid UTF-8. The decoded text is processed as data only; it is never executed or interpreted, so encoding-based injection is not a risk.
- **Error message content:** Error messages written to stderr describe the problem (e.g., file not found, permission denied) but do not expose internal stack traces or sensitive system information in production paths.

---

## Test Strategy

### Unit Tests (`tests/unit/`)

| Test File | What It Tests | Key Cases |
|---|---|---|
| `test_null_detection.py` | `is_null()` function | All six null sentinels; case variations (`NULL`, `null`, `Null`); non-null values; whitespace-only strings |
| `test_accumulator.py` | `ColumnAccumulator.update()` and `finalize()` | Numeric type inference; date type inference; text fallback; all-null column; mixed numeric+text → text; min/max/mean correctness; date min/max lexicographic correctness; distinct count correctness; null_count correctness; rounding to 2 decimal places |
| `test_reader.py` | `stream_rows()` and `open_with_encoding()` | UTF-8 file; Latin-1 file; 0-byte file yields no rows; header-only file yields one row then stops; rows with quoted commas; `FileNotFoundError` propagation |
| `test_reporter.py` | `print_report()` formatting | Numeric column section layout; text column section layout; date column section layout; total row count line; column type label accuracy |

### Integration Tests (`tests/integration/test_acceptance.py`)

Each acceptance criterion maps to one or more test functions that create temporary CSV files, invoke the full pipeline via `cli.main()` with `sys.argv` patched and `sys.stdout`/`sys.stderr` captured, and assert on output and exit code:

| Test Function | Acceptance Criterion |
|---|---|
| `test_valid_csv_summary()` | AC-1 — Valid CSV produces complete report, exit 0 |
| `test_nonexistent_file()` | AC-2 — Non-existent path → stderr message, exit 1 |
| `test_header_only_csv()` | AC-3 — Header-only file → "No data rows found.", exit 0 |
| `test_empty_file()` | AC-4 — 0-byte file → "No data rows found.", exit 0 |
| `test_numeric_column_stats()` | AC-5 — Numeric column: correct min, max, mean (2dp), null count |
| `test_text_column_stats()` | AC-6 — Text column: correct distinct count, null count |
| `test_date_column_stats()` | AC-7 — Date column: correct earliest, latest, null count |
| `test_memory_streaming()` | AC-8 — 100 MB synthetic CSV processed under 512 MB (measured via `tracemalloc`) |

---

## Open Design Questions

| ID | Question | Assumption Made | Impact if Wrong |
|---|---|---|---|
| OQ-1 | Should date earliest/latest display the full datetime string when source format is `YYYY-MM-DDTHH:MM:SS`? | Yes — display the value exactly as it appears in the CSV (from requirements OQ-1 resolution) | Minor display difference; trivially changed in `reporter.py` |
| OQ-2 | Should the report include percentage of nulls in addition to raw null count? | No — raw count only, as per acceptance criteria (from requirements OQ-2 resolution) | Low; adding a percentage column to reporter output only |
| OQ-3 | Should the `text_distinct` set be capped to prevent extreme memory usage for pathological high-cardinality text columns? | No cap is applied; accurate distinct count is preferred over memory bounding for text columns | If a text column in a 100 MB file has tens of millions of unique long strings, memory could approach the 512 MB limit; can be mitigated post-MVP with an approximate counter (HyperLogLog) if needed |
