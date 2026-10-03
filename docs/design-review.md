# Design Review

**Project:** CSV Summary Report Generator
**Reviewer:** Design Review Agent
**Date:** 2026-10-02
**Architecture version reviewed:** `docs/architecture.md` (dated 2026-10-01)
**Overall Assessment:** Approve with Changes

---

## Summary

The architecture is well-structured and appropriate for the problem scope — a single-process, stdlib-only CLI tool with streaming I/O and clear module boundaries. The highest-concern area is an ambiguity in the interface between `reader.open_with_encoding()` and `reader.stream_rows()`: the data flow describes them as two separate calls that each accept a file path, but it is not specified whether `stream_rows` accepts the `TextIO` returned by `open_with_encoding` or re-opens the file independently, and how a mid-stream `UnicodeDecodeError` triggers a clean restart of the full streaming pass. This interface gap must be resolved before implementation begins to avoid either redundant file opens or a mishandled encoding retry. Two additional minor gaps — an inconsistent accumulator interface signature and a portability gap for Windows CSV reading — are also flagged.

---

## Risk Table

| Risk | Category | Severity | Recommendation |
|---|---|---|---|
| `open_with_encoding()` returns `TextIO` but `stream_rows()` also takes a `path: str`. It is unspecified whether `stream_rows` accepts a pre-opened `TextIO` or re-opens the file, and how a `UnicodeDecodeError` that fires mid-stream (e.g., at row 5000) triggers a complete restart of the streaming pass from byte 0. | Component interfaces | Major | Clarify the interface contract: either `stream_rows` should accept a `TextIO` argument produced by `open_with_encoding`, or `open_with_encoding` should probe enough bytes to detect encoding before handing off a correctly-encoded file object. Specify in the architecture how a mid-stream encoding failure causes a clean file re-open and re-read from the header row. |
| The `accumulator.py` interface table lists `update(value: str) -> None` but the data flow description (step 7) states `cli.py` calls `accumulator.update(cell, is_null_flag)` with two arguments. | Component interfaces | Major | Correct the interface definition to `update(value: str, is_null: bool) -> None` to match the described calling convention. Ambiguous signatures at a module boundary directly cause implementation errors. |
| Python's `csv` module documentation requires files to be opened with `newline=''` to prevent Windows from translating `\r\n` to `\n` before the csv parser sees it, which can corrupt rows with embedded newlines. The architecture does not mention this requirement in `reader.py`. | Non-functional requirements (NFR-5 Portability) | Major | Add an explicit note in the `reader.py` component description and data flow that `open()` must be called with `newline=''` on all platforms. This is a documented Python requirement for correct csv parsing and is the most common cross-platform csv bug. |
| AC-8 specifies measuring memory via `tracemalloc`, but NFR-1 requires "resident memory usage" (RSS). `tracemalloc` tracks Python-level allocations only; it understates true RSS by excluding interpreter overhead, loaded modules, and OS I/O buffers. A synthetic 100 MB file with high text column cardinality could pass `tracemalloc` but exceed 512 MB RSS. | Non-functional requirements (NFR-1) | Minor | Document what the AC-8 synthetic CSV contains (column types, cardinality). If text columns with high cardinality are included, either cap the test file's distinct-value count or note the RSS vs. tracemalloc gap explicitly. Consider using `resource.getrusage` (POSIX) or `psutil` for a more accurate RSS check, or explicitly document the limitation in the test file. |
| OQ-3 acknowledges that the `text_distinct` set is unbounded. A 100 MB file composed entirely of a high-cardinality text column (e.g., UUIDs) could exhaust memory. The architecture accepts this risk without a monitoring or early-warning mechanism. | Scalability | Minor | Retain the accepted trade-off for MVP, but add a note in the architecture that this is a known post-MVP improvement point (HyperLogLog or a cap with approximate counting) and document the worst-case scenario explicitly so implementers are not surprised by OOM in edge cases. |
| The top-level `except Exception` in `cli.py` catches all unexpected errors and prints "a descriptive message." The architecture does not specify whether the exception type or message text from the original exception is included in that stderr output. Swallowing the original exception detail makes unexpected bugs silent. | Error Handling | Minor | Specify that the catch-all handler must include at minimum the exception class name and its string representation in the stderr message (e.g., `f"Unexpected error ({type(e).__name__}): {e}"`). This costs nothing and preserves debuggability without exposing stack traces to end users. |
| The error paths section does not include the case where the user supplies no argument (zero-argument invocation). The data flow mentions it ("If not provided, it prints usage to stderr and exits with code 1") but it is absent from the error paths table and from the acceptance criteria. | Scope fit | Minor | Add zero-argument invocation to the error paths table and confirm whether a corresponding acceptance criterion or unit test is needed (recommended: yes, as a one-line test in `test_cli.py` or `test_acceptance.py`). |

---

## Design Decisions Confirmed

- **Stdlib-only, single-process CLI**: Correct and necessary given NFR-4. No third-party packages are appropriate for this scope.
- **Streaming row-by-row via `csv.reader`**: The right choice for NFR-1 and NFR-2. Lazy iteration bounds peak memory to O(columns) for numeric/date columns.
- **Single-pass accumulator pattern**: Efficient and correct. Maintaining `is_all_date` / `is_all_numeric` flags that are cleared on first disqualifying value is idiomatic and avoids multi-pass overhead.
- **Type inference priority order (date > numeric > text)**: Consistent with FR-8 and FR-9. Date is checked first because all ISO 8601 dates could also be parsed as numeric strings in degenerate cases.
- **All-null column classified as text**: Matches FR-11 exactly. The finalize logic handles this cleanly.
- **`ColumnResult` dataclass as the boundary contract**: A typed, immutable data transfer object between `accumulator` and `reporter` is the right abstraction. It decouples statistics computation from presentation.
- **UTF-8 with Latin-1 fallback**: Matches FR-18. Using Latin-1 as the fallback is correct because Latin-1 accepts all byte values (0x00–0xFF), making it a safe last resort.
- **Test structure (unit + integration with AC mapping)**: The one-to-one mapping of integration test functions to acceptance criteria is clear and auditable.
- **Error message to stderr, clean stdout**: Correct separation of concerns. AC-2 explicitly verifies stdout is empty on error.
- **`re` pre-validation before `datetime.fromisoformat()`**: Justified for performance in a tight per-cell loop. Exception-driven flow for non-date values at scale would be measurably slower.
- **`dataclasses` for `ColumnResult`**: Appropriate stdlib choice for a typed result container. No external serialisation dependency is needed.

---

## Required Changes Before Implementation

**⚠ Changes required before proceeding.**

The following changes must be made to `docs/architecture.md` before the Implementation Planner agent begins its work. All three are interface or correctness gaps that, if left unresolved, will cause implementers to make inconsistent choices.

1. **Resolve the `open_with_encoding` / `stream_rows` interface contract (Major).** Specify one of the following designs and document it:
   - *Option A (recommended):* `open_with_encoding(path: str) -> TextIO` probes the first N bytes for encoding detection and returns an appropriately-encoded file object opened with `newline=''`; `stream_rows(file: TextIO) -> Iterator[list[str]]` wraps `csv.reader` around the caller-supplied file object. `cli.py` owns the `with` block. If encoding detection via probing is insufficient, document the fallback retry behaviour.
   - *Option B:* `stream_rows(path: str) -> Iterator[list[str]]` encapsulates both encoding detection and streaming internally, retrying the entire file from the beginning on `UnicodeDecodeError`, and `open_with_encoding` is removed as a public interface. `cli.py` calls only `stream_rows`.
   In either case, the architecture must describe how a `UnicodeDecodeError` that fires after the header row has already been yielded is handled without data loss or corruption.

2. **Correct the `accumulator.update()` interface signature (Major).** Change the interface table entry from `update(value: str) -> None` to `update(value: str, is_null: bool) -> None` to match the data flow description in step 7. If the intended design is that `update` calls `is_null()` internally, update the data flow and remove the two-argument call from step 7.

3. **Add `newline=''` portability requirement to `reader.py` (Major).** Add an explicit statement in the `reader.py` component description that all `open()` calls must use `newline=''` per the Python `csv` module documentation. Without this, the tool will mishandle files with embedded newlines on Windows, violating NFR-5.
