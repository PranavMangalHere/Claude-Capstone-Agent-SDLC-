---
name: code-review
description: Structured code review across 8 areas — correctness, security, error handling, test coverage, clarity, DRY, dependency safety, and Python conventions
---

## Role

Act as a senior Python engineer performing a pre-merge code review. Your job is to find real defects and quality gaps — not to nitpick style or invent hypothetical issues.

---

## Input

- `src/` — all source files to review
- `tests/` — all test files
- `docs/requirements.md` — the spec to review against (not assumptions)

---

## Review Process

1. **Read `docs/requirements.md` first** — every finding must be anchored to a requirement or an objective quality standard, not an opinion.
2. **Read all files in `src/` and `tests/`** before writing any findings.
3. **Work through each review area below** in order. For each area, check every applicable file.
4. **Only report actual findings** — if an area has no issues, write "No findings." Do not pad the report.
5. **Assign severity** using the definitions below — do not inflate or deflate severity.

---

## Severity Definitions

| Severity | Definition |
|---|---|
| **Critical** | Breaks functionality OR exposes a security risk. Must be fixed before merge. |
| **Major** | Degrades reliability, maintainability, or test coverage significantly. Should be fixed before merge. |
| **Minor** | Style, clarity, or DRY issue that does not affect correctness. Fix if straightforward. |

---

## Review Areas

### 1. Correctness
- Does each component behave as specified in `docs/requirements.md`?
- Are all functional requirements implemented? Note any that are missing entirely.
- Are edge cases handled: empty input, null/None values, boundary values, invalid types?

### 2. Security
- Are secrets (API keys, passwords, tokens) excluded from source code and output?
- Is all user-supplied input validated before use (type check, range check, format check)?
- Are file paths sanitized to prevent directory traversal?
- Is output sanitized before writing to files or stdout?
- Are subprocess calls avoided, or if present, are they safe (no shell=True with user input)?

### 3. Error Handling
- Are external calls (file I/O, network, subprocess) wrapped in try/except with specific exception types?
- Are errors surfaced to the caller or user with a meaningful message — not silently swallowed?
- Are there bare `except:` clauses? (Flag as Major — catches SystemExit and KeyboardInterrupt)
- Does the program exit with a non-zero code on failure?

### 4. Test Coverage
- Does the test suite cover the happy path for every functional requirement?
- Are key edge cases tested: empty input, invalid format, missing file, unexpected type?
- Are tests isolated — no test depends on the side effects of another?
- Are fixtures and mocks used correctly — not hiding real behavior?

### 5. Code Clarity
- Are function and variable names self-explanatory (no single-letter names outside loops)?
- Is logic followable without needing comments to decode it?
- Are functions short enough to read in one screen (~40 lines max)?
- Are magic numbers or strings replaced with named constants?

### 6. DRY Principle
- Is there duplicated logic that appears in two or more places and should be a shared function?
- Are similar patterns repeated across files that suggest a missing abstraction?

### 7. Dependency Safety
- Are all third-party packages listed in `pyproject.toml` with pinned or bounded versions?
- Are any imported packages not listed in `pyproject.toml`?
- Do any packages have known critical vulnerabilities in the version used? (Check against common knowledge — do not hallucinate CVEs.)

### 8. Python Conventions
- Is the code PEP 8 compliant (naming, spacing, line length ≤ 88 chars)?
- Do all public functions and classes have type hints on parameters and return values?
- Are there mutable default arguments (e.g., `def f(x=[])`)? (Flag as Major)
- Are f-strings used instead of `%` formatting or `.format()` where applicable?

---

## Output Format

Write the output to `output/reports/code-review.md` using this exact structure:

```markdown
# Code Review Report

**Date**: [date]
**Reviewed**: `src/` + `tests/`
**Spec**: `docs/requirements.md`
**Overall Result**: APPROVE / REQUEST CHANGES

---

## Summary

[2–3 sentences: what the code does well, and the headline issues if any]

---

## Findings

### 1. Correctness
| Severity | File | Line | Description | Suggestion |
|---|---|---|---|---|
| Critical/Major/Minor | `src/foo.py` | 42 | [What is wrong] | [How to fix it] |

*(or: "No findings.")*

### 2. Security
...

### 3. Error Handling
...

### 4. Test Coverage
...

### 5. Code Clarity
...

### 6. DRY Principle
...

### 7. Dependency Safety
...

### 8. Python Conventions
...

---

## Overall Recommendation

**APPROVE** — No Critical or Major findings. Ready to merge.

*or*

**REQUEST CHANGES** — [N] Critical, [N] Major findings must be resolved before merge.

Critical findings:
- [Finding ID / short description]
```

---

## Rules

- Only report findings you can point to with a specific file and line — no hypothetical issues
- Always review against `docs/requirements.md`, not against what you think the code *should* do
- Severity = Critical only for broken functionality or security exposure — do not inflate
- If a finding in one area implies another area is also affected, report it in both areas
