---
name: verification
description: Run the test suite, validate acceptance criteria coverage, and produce a structured pass/fail results report
---

## Role

Act as a QA engineer running final acceptance testing. Your job is to verify that the implementation passes all tests, meets coverage thresholds, and satisfies every acceptance criterion in the requirements — then produce an unambiguous PASS or FAIL verdict.

---

## Input

- `src/` — source code to test
- `tests/` — test suite (unit + integration)
- `docs/requirements.md` — acceptance criteria to verify against

---

## Verification Steps

Run these steps in order. If any step fails, continue through all remaining steps — record all failures, do not stop early.

### Step 1 — Unit Tests
```
pytest tests/unit/ -v
```
- Record: total tests, passed, failed, skipped, and any error output for failed tests
- A test that errors (not just fails) counts as a failure

### Step 2 — Integration Tests
```
pytest tests/integration/ -v
```
- Record: total tests, passed, failed, skipped
- If `tests/integration/` is empty, note it explicitly — do not skip silently

### Step 3 — Coverage
```
pytest --cov=src --cov-report=term-missing tests/
```
- Record: overall coverage %, and per-module breakdown
- Flag any module below 80% individually

### Step 4 — Acceptance Criteria Coverage
- Read every acceptance criterion from `docs/requirements.md`
- For each criterion, identify which test(s) exercise it (by test name and file)
- If no test covers a criterion, it is a **gap** — flag it regardless of overall coverage %

### Step 5 — Open Code Review Findings
- Check `output/reports/code-review.md` for any Critical findings marked as unresolved
- If any Critical findings are open, the verification verdict is FAIL regardless of test results

---

## Pass Criteria

All of the following must be true for a PASS verdict:

| Gate | Threshold |
|---|---|
| Unit tests | 0 failures, 0 errors |
| Integration tests | 0 failures, 0 errors |
| Overall coverage | ≥ 80% |
| Acceptance criteria coverage | Every criterion covered by ≥ 1 test |
| Open Critical findings | 0 |

If any gate fails, the verdict is **FAIL**.

---

## Output Format

Write the output to `output/test-results/results.md` using this exact structure:

```markdown
# Verification Results

**Date**: [date]
**Verdict**: PASS / FAIL

---

## Test Run Summary

| Suite | Total | Passed | Failed | Skipped | Errors |
|---|---|---|---|---|---|
| Unit | N | N | N | N | N |
| Integration | N | N | N | N | N |
| **Total** | N | N | N | N | N |

### Failed Tests

| Test Name | File | Error / Assertion Message |
|---|---|---|
| test_foo_bar | `tests/unit/test_foo.py` | AssertionError: expected 3, got 2 |

*(or: "None.")*

---

## Coverage Report

**Overall**: XX%

| Module | Coverage % | Missing Lines |
|---|---|---|
| `src/module.py` | XX% | 42–47, 93 |

**Modules below 80%**:
- `src/module.py` — XX% (BELOW THRESHOLD)

*(or: "All modules meet the 80% threshold.")*

---

## Acceptance Criteria Coverage

| Criterion ID | Criterion (short) | Covered By | Status |
|---|---|---|---|
| FR-01 | [Short name] | `test_foo` in `tests/unit/test_foo.py` | Covered |
| FR-02 | [Short name] | — | GAP |

---

## Gaps

| Gap Type | Detail |
|---|---|
| Uncovered criterion | FR-02 has no test |
| Below-threshold module | `src/bar.py` at 61% |
| Open Critical finding | [finding description from code-review.md] |

*(or: "None — all gates passed.")*

---

## Gate Summary

| Gate | Result |
|---|---|
| Unit tests | PASS / FAIL |
| Integration tests | PASS / FAIL |
| Coverage ≥ 80% | PASS / FAIL |
| All criteria covered | PASS / FAIL |
| No open Critical findings | PASS / FAIL |

**Final Verdict: PASS / FAIL**
```

---

## Rules

- Never mark a verdict as PASS unless every gate passes — partial passes are still FAIL
- Run all 5 steps even if early steps fail — report the complete picture
- Do not infer test coverage from reading test files — run the commands and use actual output
- If `tests/integration/` is empty, the integration gate is a **gap**, not a pass
- Report exact pytest output for any failed test — do not paraphrase error messages
