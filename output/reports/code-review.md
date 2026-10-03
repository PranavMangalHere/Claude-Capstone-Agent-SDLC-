# Code Review Report

**Date**: 2026-10-03
**Reviewed**: `src/csv_summary/` + `tests/`
**Spec**: `docs/requirements.md`
**Overall Result**: REQUEST CHANGES

---

## Summary

The implementation is well-structured, cleanly modular, and handles most functional requirements correctly. The streaming design, encoding fallback, and error handling pipeline are all sound. However, there is one Major correctness defect in the distinct-value counting logic for text columns that transition from appearing numeric/date mid-stream (FR-6 violation), and one Major test coverage gap — the Latin-1 encoding fallback (FR-18) is never exercised end-to-end through `cli.main()`.

---

## Findings

### 1. Correctness

| Severity | File | Line | Description | Suggestion |
|---|---|---|---|---|
| Major | `src/csv_summary/accumulator.py` | 113–117 | **FR-6 violation: `text_distinct_count` undercount for columns that transition from numeric/date to text.** When a column's first values parse as numeric (e.g., `"42"`) but a later value is non-numeric (e.g., `"hello"`), the numeric values seen before the transition are never added to `text_distinct`. For the column `["42", "hello", "world"]` the implementation returns `distinct=2` instead of the correct `3`. The design comment acknowledges this but the spec requires accurate distinct counts with no such exception. | Backfill values into `text_distinct` at the moment the column is reclassified from numeric or date to text, using the accumulated numeric/date values already held in the accumulator (e.g., retain seen values in a buffer until type is confirmed, then flush). |
| Minor | `src/csv_summary/cli.py` | 83 | The compound boolean `total_rows == -1 or total_rows == 0 and not results` relies on implicit operator precedence (`and` binds tighter than `or`). This is correct but fragile and hard to read at a glance. | Parenthesize explicitly: `(total_rows == -1) or (total_rows == 0 and not results)`. |

**Narrative**

FR-1 through FR-5, FR-7 through FR-15 are correctly implemented. The date regex (`^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?$`) combined with `datetime.fromisoformat` correctly validates both ISO date formats per FR-8. FR-11 (all-null columns → text, distinct=0) is correct. FR-14 (0-byte and header-only → "No data rows found.", exit 0) is correct, using the sentinel `-1` for empty files and a second `if total_rows == 0:` guard for header-only files. FR-18 (UTF-8 → Latin-1 fallback) is implemented correctly in `_process_file`.

The one genuine FR-6 correctness defect: `text_distinct` is populated only once both `is_all_numeric` and `is_all_date` are False (line 116). Values seen while either flag is still True are never added to the set. The column type can transition to text on any non-first row, so all values before that row are silently excluded from the distinct count.

---

### 2. Security

No findings.

**Narrative**

No secrets or credentials are present in source code. There are no subprocess calls. The generic top-level `except Exception` handler in `cli.py` (line 105) prints the exception class name and message; for a local CLI tool processing user-owned files this is acceptable. File paths come directly from `sys.argv` without sanitisation, which is standard and expected for a CLI tool of this kind.

---

### 3. Error Handling

No findings.

**Narrative**

All error paths required by FR-13 and FR-15 are handled with specific exception types: `FileNotFoundError`, `PermissionError`, `csv.Error`, and `UnicodeDecodeError` each have their own `except` clause with a descriptive message to stderr and `sys.exit(1)`. The fallback `except Exception` at line 105 is at the outermost layer of a CLI entry point and is not a bare `except:`. The UTF-8 → Latin-1 retry in `_process_file` correctly catches `UnicodeDecodeError` raised during lazy streaming iteration, not just at file-open time.

---

### 4. Test Coverage

| Severity | File | Line | Description | Suggestion |
|---|---|---|---|---|
| Major | `tests/` (all) | — | **FR-18 has no end-to-end test.** `test_reader.py::TestOpenWithEncoding::test_latin1_file_readable_with_latin1_encoding` only verifies that `open_with_encoding` can open a Latin-1 file when the encoding is passed explicitly. No test creates a Latin-1-encoded CSV, invokes `cli.main()`, and asserts that the fallback fires and the file is processed successfully. | Add an integration test: write a CSV containing a Latin-1 byte sequence (e.g., `b"name\ncaf\xe9\n"`), run `run_main_captured(["csv_summary", str(path)], capsys)`, and assert exit_code=0 and "caf" in stdout. |
| Minor | `tests/integration/test_acceptance.py` | 26–34 | `run_main()` (without `capsys`) always returns `("", "")` as stdout/stderr regardless of actual program output, making the return signature misleading. It is called in only one place without inspecting the returned strings, but the signature implies captured values are available. | Either remove the return values (`return exit_code` only), or use `capsys` and actually capture; the duplicate `run_main_captured` already handles the capturing case. |
| Minor | `tests/unit/test_accumulator.py` | 124–161 | No test for the mixed-column distinct undercount scenario described in the Correctness finding (e.g., `["42", "hello"]` with numeric value first). The existing `test_mixed_values_classified_as_text` uses `["hello", "42"]` (text-first), which avoids the defect path. | Add a test with values in numeric-first order to expose the FR-6 undercount. |

**Narrative**

Coverage is strong overall: FR-1 through FR-15 each have at least one traceable test, including edge cases for 0-byte files (AC-4), header-only files (AC-3), all-null columns (FR-11), mixed types (FR-10), and ISO datetime variants (FR-8). The AC-8 memory test correctly uses `tracemalloc` and notes its limitations. The null sentinel tests cover all six sentinels in uppercase, mixed-case, and whitespace-padded forms. The principal gap is the missing CLI-level Latin-1 fallback test.

---

### 5. Code Clarity

No findings.

**Narrative**

Module responsibilities are cleanly separated: `null_detection`, `accumulator`, `reader`, `reporter`, and `cli` each own a single concern. Function names (`stream_rows`, `open_with_encoding`, `is_null`, `finalize`, `print_report`) are self-explanatory. Functions are short and readable. The design-note comment inside `ColumnAccumulator` correctly documents the intent behind the `text_distinct` population strategy, even though the strategy conflicts with the spec.

---

### 6. DRY Principle

No findings.

**Narrative**

No significant duplication exists across the source modules. The two test helpers `run_main` and `run_main_captured` in the integration tests serve different purposes and are not candidates for unification without restructuring the capture mechanics.

---

### 7. Dependency Safety

No findings.

**Narrative**

`pyproject.toml` declares `dependencies = []` and `requires-python = ">=3.9"`. Every import across all source files (`csv`, `pathlib`, `re`, `datetime`, `dataclasses`, `logging`, `sys`, `typing`) is from the Python standard library. NFR-4 (stdlib-only) and NFR-3 (Python 3.9+) are satisfied.

---

### 8. Python Conventions

| Severity | File | Line | Description | Suggestion |
|---|---|---|---|---|
| Minor | `src/csv_summary/reporter.py` | 6 | `import sys` is present but `sys` is never referenced in the file. All output goes through `print()` with no explicit `file=` argument. | Remove the unused import. |
| Minor | `src/csv_summary/cli.py` | 9 | `from csv_summary import accumulator as acc_module` is imported but the alias `acc_module` is never referenced. `ColumnAccumulator` and `ColumnResult` are imported directly on line 13. | Remove line 9; the direct imports on line 13 are sufficient. |

**Narrative**

Type hints are present on all public functions. `from __future__ import annotations` is used consistently for forward-reference compatibility with Python 3.9. No mutable default arguments were found. f-strings are used throughout. The `Optional[float]` and `List[...]` typing forms are appropriate for the Python 3.9 minimum target. Line lengths appear within the 88-character limit configured in `pyproject.toml`. Two unused imports are the only convention violations.

---

## Overall Recommendation

**REQUEST CHANGES** — 2 Critical, 2 Major findings must be resolved before merge.

Wait — correcting severity: 0 Critical, 2 Major findings.

**REQUEST CHANGES** — 2 Major findings must be resolved before merge.

Major findings:
- **FR-6 correctness violation** (`accumulator.py` lines 113–117): `text_distinct_count` is undercounted for columns that see numeric- or date-parseable values before transitioning to text type. The column `["42", "hello", "world"]` returns `distinct=2` instead of `3`.
- **FR-18 test coverage gap** (no test file): The CLI-level UTF-8 → Latin-1 encoding fallback path is never exercised through `cli.main()`. Only the lower-level `open_with_encoding` function is tested with an explicitly specified encoding.
