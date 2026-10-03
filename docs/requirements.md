# Requirements

**Project:** CSV Summary Report Generator  
**Source:** `user-stories/user-story-template.md`  
**Author:** Requirements Agent  
**Date:** 2026-10-01

---

## Functional Requirements

| ID   | Requirement | Priority |
|------|-------------|----------|
| FR-1 | The tool shall be invocable from the command line as `python -m csv_summary <path-to-csv>`. | High |
| FR-2 | The tool shall read the specified CSV file and print a human-readable summary report to stdout. | High |
| FR-3 | The report shall include the total number of data rows, excluding the header row. | High |
| FR-4 | The report shall list every column name along with its inferred data type (one of: `numeric`, `text`, `date`). | High |
| FR-5 | For each `numeric` column the report shall display: minimum value, maximum value, arithmetic mean (rounded to 2 decimal places), and count of null values. | High |
| FR-6 | For each `text` column the report shall display: count of distinct non-null values and count of null values. | High |
| FR-7 | For each `date` column the report shall display: earliest date, latest date, and count of null values. | High |
| FR-8 | A column is classified as `date` if and only if every non-null value in that column conforms to ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`). No other date formats trigger `date` classification. | High |
| FR-9 | A column is classified as `numeric` if every non-null value can be parsed as an integer or floating-point number and the column is not already classified as `date`. | High |
| FR-10 | A column that contains a mix of numeric and text values, or that does not meet the criteria for `numeric` or `date`, shall be classified as `text`. | High |
| FR-11 | A column whose every value is null shall be classified as `text` and reported with unique count 0 and null count equal to the total row count. | Medium |
| FR-12 | The following cell values shall be treated as null (case-insensitive): empty string, `NULL`, `N/A`, `NA`, `nan`, `none`. | High |
| FR-13 | If the specified file does not exist, the tool shall print a descriptive error message to stderr and exit with code 1. | High |
| FR-14 | If the file exists but is completely empty (0 bytes) or contains only a header row (1 row, no data rows), the tool shall print "No data rows found." to stdout and exit with code 0. | High |
| FR-15 | All error conditions not covered by FR-13 and FR-14 (e.g., permission denied, malformed CSV, unreadable encoding) shall print a descriptive error message to stderr and exit with code 1. | High |
| FR-16 | The tool shall assume the first row of every CSV file is a header row. There is no `--no-header` flag in this version. | Medium |
| FR-17 | The tool shall process files using comma (`,`) as the delimiter. No other delimiter or auto-detection is supported in this version. | Medium |
| FR-18 | The tool shall read the input file in UTF-8 encoding, falling back to Latin-1 (`ISO-8859-1`) if UTF-8 decoding fails. | Medium |

---

## Non-Functional Requirements

| ID    | Category      | Requirement |
|-------|---------------|-------------|
| NFR-1 | Performance   | The tool shall process a CSV file of up to 100 MB without exceeding 512 MB of resident memory usage. |
| NFR-2 | Performance   | The tool shall use chunk-based or streaming file reading to satisfy NFR-1; it must not load the entire file into memory at once. |
| NFR-3 | Compatibility | The tool shall be compatible with Python 3.9 and above. |
| NFR-4 | Dependencies  | The tool shall rely only on the Python standard library. No third-party packages (e.g., pandas, numpy) are permitted. |
| NFR-5 | Portability   | The tool shall run on Linux, macOS, and Windows without platform-specific modifications. |
| NFR-6 | Usability     | The report printed to stdout shall be plain text, formatted in a human-readable tabular or sectioned layout. No machine-readable output format (JSON, CSV) is required in this version. |
| NFR-7 | Correctness   | Floating-point statistics (min, max, mean) shall be displayed rounded to exactly 2 decimal places. |
| NFR-8 | Exit codes    | Exit code 0 indicates success or an expected empty-file condition. Exit code 1 indicates any error. No other exit codes are used. |

---

## Out of Scope

- Support for delimiters other than comma (semicolons, tabs, pipes, etc.)
- Auto-detection of delimiters
- A `--no-header` flag or handling of header-less CSV files
- Date formats other than ISO 8601
- Machine-readable output formats (JSON, XML, CSV)
- A `--format` output flag
- Processing of multiple input files in a single invocation
- Writing the report to a file (only stdout is supported)
- Third-party library usage (pandas, numpy, etc.)
- Statistical measures beyond min, max, mean (e.g., median, standard deviation, percentiles)
- Column filtering or selective reporting

---

## Acceptance Criteria

**AC-1** — Valid CSV produces a summary report (maps to FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7)
```
Given a well-formed CSV file with at least one data row
When the user runs `python -m csv_summary <path>`
Then the tool exits with code 0
And stdout contains: total row count, each column name with inferred type,
  and per-column statistics appropriate to that type
And nothing is printed to stderr
```

**AC-2** — Non-existent file path (maps to FR-13)
```
Given a file path that does not exist on the filesystem
When the user runs `python -m csv_summary <path>`
Then the tool exits with code 1
And a descriptive error message is printed to stderr
And nothing is printed to stdout
```

**AC-3** — CSV with only a header row (maps to FR-14)
```
Given a CSV file that contains exactly one row (the header) and no data rows
When the user runs `python -m csv_summary <path>`
Then the tool exits with code 0
And stdout contains exactly "No data rows found."
```

**AC-4** — Completely empty file (maps to FR-14)
```
Given a CSV file that is 0 bytes in size
When the user runs `python -m csv_summary <path>`
Then the tool exits with code 0
And stdout contains "No data rows found."
```

**AC-5** — Numeric column statistics (maps to FR-5, FR-9, FR-12)
```
Given a CSV with a column where all non-null values are valid numbers
When the summary report is produced
Then that column is labelled "numeric"
And the report shows the correct min, max, mean (2 decimal places), and null count
```

**AC-6** — Text column statistics (maps to FR-6, FR-10, FR-12)
```
Given a CSV with a column that contains mixed or purely textual values
When the summary report is produced
Then that column is labelled "text"
And the report shows the correct count of unique non-null values and null count
```

**AC-7** — Date column statistics (maps to FR-7, FR-8, FR-12)
```
Given a CSV with a column where all non-null values are ISO 8601 dates
When the summary report is produced
Then that column is labelled "date"
And the report shows the correct earliest date, latest date, and null count
```

**AC-8** — Memory constraint for large files (maps to NFR-1, NFR-2)
```
Given a CSV file of 100 MB
When the tool processes it
Then peak resident memory usage does not exceed 512 MB at any point during execution
```

---

## Assumptions

| ID  | Assumption |
|-----|------------|
| A-1 | The user replied "yes" to all clarifying questions, interpreted as acceptance of the defaults documented in this file. |
| A-2 | The first row of every input CSV is always a header row; header-less files are not a supported use case. |
| A-3 | Only comma (`,`) is used as a delimiter; other delimiters are out of scope. |
| A-4 | Only ISO 8601 date strings (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`) qualify a column as type `date`. |
| A-5 | Null values are identified by: empty string, `NULL`, `N/A`, `NA`, `nan`, `none` (all case-insensitive). |
| A-6 | All-null columns are classified as `text`. |
| A-7 | Only standard library modules are available; no third-party packages are installed. |
| A-8 | UTF-8 is the primary encoding; Latin-1 is the fallback. |
| A-9 | A zero-byte file and a header-only file are both treated as "no data" and produce exit code 0. |
| A-10 | All non-success error conditions (file not found, permission denied, parse error, encoding failure) produce exit code 1. |

---

## Open Questions

| ID  | Question | Impact if Unresolved |
|-----|----------|----------------------|
| OQ-1 | Should a column classified as `date` also show the time component in its earliest/latest values when the source format is `YYYY-MM-DDTHH:MM:SS`? | Minor display difference; assumed yes — display full value as stored. |
| OQ-2 | Should the report include a column for the percentage of null values in addition to the raw count? | Low; raw count alone is implemented per the acceptance criteria. |
