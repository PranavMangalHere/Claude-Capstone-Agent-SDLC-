---
name: documentation-sync
description: Diff actual source code against existing docs and update only the sections that are out of sync — without losing design decisions
---

## Role

Act as a technical writer reviewing code changes. Your job is to keep `docs/` accurate and current after implementation, without rewriting content that is still correct and without losing documented design decisions.

---

## Input

- `src/` directory — the actual implemented source code (source of truth)
- `docs/` directory — the existing documentation files to check and update

---

## Sync Process

Work through these steps in order:

1. **Read all files in `src/`** — understand what was actually built: modules, classes, functions, signatures, dependencies used.
2. **Read all files in `docs/`** — understand what was documented: requirements, architecture, design decisions, impl plan.
3. **Diff code against docs** — identify every discrepancy in these categories:

   | Category | What to Look For |
   |---|---|
   | New additions | Functions, classes, or modules in `src/` not mentioned in any doc |
   | Removals | Functions, classes, or modules referenced in docs that no longer exist in `src/` |
   | Signature changes | Function parameters or return types that differ from what docs describe |
   | New dependencies | Third-party packages imported in `src/` not listed in `docs/architecture.md` |
   | Removed dependencies | Packages listed in docs no longer imported in `src/` |
   | Behavior changes | Implementation logic that contradicts what a doc says the component does |

4. **Update only affected sections** — edit the specific section of the specific doc that is wrong. Do not rewrite unaffected sections.
5. **Preserve design decisions** — if a doc section explains *why* a choice was made, keep that reasoning even if the surrounding facts changed. Never delete rationale.
6. **Mark deprecated items** — if something was removed from code but was a documented design decision, do not delete it from the doc. Add `[DEPRECATED as of implementation]` inline and keep the entry.
7. **Write the sync report** — after updating docs, produce a summary of every change made.

---

## Output

### Updated doc files
Edit `docs/architecture.md`, `docs/requirements.md`, or `docs/impl-plan.md` in place — only the sections that changed.

### Sync report (append to `docs/changelog.md`)

```markdown
## Documentation Sync — [date]

### Changes Made

| Doc File | Section | Change Type | Description |
|---|---|---|---|
| `docs/architecture.md` | Component Descriptions | Updated | Added `ReportFormatter` component — not in original design |
| `docs/architecture.md` | Technology Choices | Added | `rich` package added for terminal output |
| `docs/impl-plan.md` | Task T-03 | Deprecated | `CacheManager` was removed during implementation |

### No Changes Needed

[List any doc sections explicitly checked and confirmed still accurate]

### Open Gaps

[Any discrepancy found that could not be resolved without human input]
```

---

## Rules

- **Never delete documented design decisions** — mark as `[DEPRECATED]`, never remove
- **Never rewrite sections that are still accurate** — targeted edits only
- **Never add padding** — do not expand docs with obvious or redundant information
- **Source of truth is `src/`** — if code and docs conflict, the code is correct
- **Do not infer intent** — if a change in code is ambiguous (renamed vs. replaced?), note it as an open gap rather than guessing
