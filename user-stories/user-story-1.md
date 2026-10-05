# User Story 1: CSV Summary Report Generator

## Title
Build a Python CLI tool that reads CSV files, analyzes data, and generates comprehensive summary reports in multiple formats.

---

## Background

Data analysts and engineers frequently need to quickly understand the contents of CSV files without opening them manually. They need:
- Quick overview statistics (row count, column info)
- Data quality insights (missing values, duplicates, data types)
- Numeric summaries (min, max, mean, median for numeric columns)
- Categorical insights (value counts, top categories)
- Export in multiple formats for easy sharing

---

## User Story

**As a** data analyst or engineer  
**I want to** run a CLI command on a CSV file to get a comprehensive summary report  
**So that** I can quickly understand the data without manual inspection or loading it into external tools

---

## Acceptance Criteria

### Core Functionality
- [ ] CLI accepts a CSV file path as input
- [ ] Tool reads the CSV and analyzes all columns
- [ ] Tool generates a summary report including:
  - **File Info**: filename, row count, column count, file size
  - **Column Details**: column names, data types, missing value count, missing %
  - **Numeric Columns**: min, max, mean, median, std dev
  - **Categorical Columns**: value counts (top 10), unique value count
  - **Data Quality**: duplicate row count, empty row count

### Output Formats
- [ ] Default output: Pretty-printed text to stdout
- [ ] JSON format: `--format json` saves to `<filename>_summary.json`
- [ ] CSV format: `--format csv` saves statistics as CSV rows to `<filename>_summary.csv`

### Error Handling
- [ ] Graceful handling of file not found (clear error message)
- [ ] Graceful handling of invalid CSV format (skip bad rows, report count)
- [ ] Graceful handling of permission errors
- [ ] Graceful handling of very large files (should not crash, stream if needed)

### Performance
- [ ] Should handle CSV files up to 100MB without excessive memory use
- [ ] Analysis should complete in <5 seconds for typical files

### Logging & Debugging
- [ ] Verbose mode: `--verbose` flag for detailed processing logs
- [ ] All errors logged to stderr, results to stdout
- [ ] Clear progress indication for large files

---

## Example Usage

```bash
# Basic usage - prints to stdout
python -m csv_summary input.csv

# Output to JSON
python -m csv_summary input.csv --format json

# Output to CSV
python -m csv_summary input.csv --format csv

# Verbose mode
python -m csv_summary input.csv --verbose
```

---

## Example Output (Text Format)

```
================================================================================
                         CSV Summary Report
================================================================================
File: sales_data.csv
Rows: 10,542 | Columns: 8 | Size: 2.3 MB

================================================================================
                          Column Analysis
================================================================================

[0] date (date)
    Missing: 0 (0.0%)
    Unique: 365
    Min: 2023-01-01 | Max: 2023-12-31

[1] product_id (int)
    Missing: 15 (0.14%)
    Unique: 847
    Min: 1001 | Max: 9999 | Mean: 5423.45 | Median: 5500

[2] product_name (string)
    Missing: 0 (0.0%)
    Unique: 847
    Top Values:
      - Widget A: 234 (2.2%)
      - Widget B: 198 (1.9%)
      - Gadget X: 187 (1.8%)

[3] quantity (int)
    Missing: 0 (0.0%)
    Unique: 42
    Min: 1 | Max: 100 | Mean: 15.3 | Median: 12

[4] price (float)
    Missing: 0 (0.0%)
    Unique: 256
    Min: 9.99 | Max: 999.99 | Mean: 245.67 | Median: 199.99

[5] total_amount (float)
    Missing: 0 (0.0%)
    Unique: 5842
    Min: 9.99 | Max: 99,999.00 | Mean: 3,765.43 | Median: 2,499.99

[6] region (string)
    Missing: 42 (0.4%)
    Unique: 5
    Distribution:
      - North: 3245 (30.8%)
      - South: 2891 (27.4%)
      - East: 2567 (24.4%)
      - West: 1890 (17.9%)
      - Central: 8 (0.1%) [Missing: 42]

[7] salesman_id (int)
    Missing: 0 (0.0%)
    Unique: 156
    Min: 101 | Max: 256 | Mean: 178.9 | Median: 180

================================================================================
                        Data Quality Summary
================================================================================
Total Rows: 10,542
Duplicate Rows: 3
Empty Rows: 0
Rows with Missing Values: 57 (0.54%)
Complete Rows: 10,485 (99.46%)

================================================================================
```

---

## Technical Constraints

- **Language**: Python 3.9+
- **Dependencies**: Minimal (pandas optional, use stdlib CSV module as baseline)
- **No external API calls**
- **No database requirements**
- **Cross-platform** (Windows, macOS, Linux)

---

## Non-Functional Requirements

- **Code Quality**: Type hints required, PEP 8 compliant
- **Test Coverage**: Minimum 80% coverage
- **Error Messages**: Clear, actionable, user-friendly
- **Documentation**: Docstrings for all functions, README with examples
- **Performance**: Should not consume >500MB RAM for files up to 100MB

---

## Out of Scope

- ❌ Real-time file monitoring
- ❌ Database connectivity
- ❌ Machine learning insights
- ❌ Charting/visualization (text-only output for now)
- ❌ Streaming from URLs (local files only)
- ❌ Multi-threaded processing

---

## Deliverables

1. **Source Code** (`src/`):
   - `csv_summary/` package
   - `csv_summary/analyzer.py` — core analysis logic
   - `csv_summary/formatter.py` — output formatting
   - `csv_summary/cli.py` — CLI interface
   - `csv_summary/__main__.py` — entry point

2. **Tests** (`tests/`):
   - Unit tests for analyzer
   - Unit tests for formatter
   - Integration tests for CLI
   - Test fixtures with sample CSVs

3. **Documentation**:
   - `README.md` with usage examples
   - Docstrings in all modules
   - Architecture diagram

4. **CI/CD**:
   - GitHub Actions workflow (pytest + coverage)

---

## Success Criteria

- ✅ All acceptance criteria met
- ✅ Tests passing (80%+ coverage)
- ✅ Code review approved
- ✅ README and docstrings complete
- ✅ Handles edge cases gracefully
- ✅ Performance meets targets
