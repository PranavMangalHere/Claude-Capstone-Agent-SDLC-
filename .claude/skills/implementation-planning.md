---
name: implementation-planning
description: Break an approved architecture into a dependency-ordered, complexity-estimated task list ready for implementation
---

## Role

Act as a senior engineering lead doing sprint planning. Your job is to convert an approved architecture and design review into a concrete, ordered task list that a developer can execute sequentially without blocked decisions.

---

## Input

- `docs/architecture.md` (required)
- `docs/design-review.md` (required — incorporate all flagged risks and required changes before planning)

---

## Planning Process

1. **Read both input documents fully** before writing any tasks.
2. **Resolve design-review findings first** — if the design review flagged changes, ensure the plan reflects the corrected design, not the original.
3. **List all implementation tasks** — one task = one cohesive unit of work a developer can complete and test independently.
4. **Identify dependencies** — for each task, note which other tasks must be complete before it can start. A task with no dependencies can start immediately.
5. **Order tasks topologically** — dependencies first, dependents after. No task should appear before a task it depends on.
6. **Estimate complexity**:
   - **S** — a few focused functions, under ~2 hours
   - **M** — a full module with tests, ~half a day
   - **L** — multiple interconnected modules, up to 1 day
   - If any task would exceed 1 day, split it.
7. **Pair test tasks** — every implementation task must have a corresponding test task. Test tasks depend on their paired implementation task.
8. **Flag blocked tasks** — if a task depends on an external factor (API key, third-party service, human decision), flag it explicitly.

---

## Output Format

Write the output to `docs/impl-plan.md` using this exact structure:

```markdown
# Implementation Plan

## Task List

| ID | Task Name | Description | Depends On | Complexity | File(s) Affected |
|---|---|---|---|---|---|
| T-01 | [Name] | [What to build] | None | S/M/L | `src/module.py` |
| T-02 | [Name] | [What to build] | T-01 | S/M/L | `src/other.py` |
| T-01-TEST | Test: [Name] | Unit + integration tests for T-01 | T-01 | S/M | `tests/unit/test_module.py` |

*(Implementation tasks use T-XX. Test tasks use T-XX-TEST. Order rows by execution order.)*

## Dependency Graph

```
T-01 ──► T-02 ──► T-03
  │                 │
  └──► T-01-TEST    └──► T-03-TEST
```

## Blocked Tasks

| Task ID | Blocked By | Resolution Needed |
|---|---|---|
| T-XX | [External factor] | [What needs to happen to unblock] |

*(If none: "None — all tasks are unblocked.")*

## Definition of Done

The implementation is complete when:
- [ ] All T-XX tasks are implemented and passing their paired T-XX-TEST tasks
- [ ] `pytest tests/` exits with 0 failures
- [ ] All files listed in "File(s) Affected" exist and are non-empty
- [ ] Every functional requirement in `docs/requirements.md` is traceable to at least one task
```

---

## Rules

- Each task must result in **runnable, testable code** — no "scaffold only" tasks
- No task larger than **1 day of focused work** — split if needed
- Test tasks are **mandatory** for every implementation task; never omit them
- The ordered task list must be a valid **topological sort** — verify no task appears before its dependency
- Do not plan for features not in `docs/architecture.md` — scope is fixed at this stage
