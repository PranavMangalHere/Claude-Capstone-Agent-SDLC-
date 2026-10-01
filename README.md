# Automated Documentation Sync — Agentic SDLC Pipeline

## What This Is

A Claude Code-native pipeline that takes any Python project user story and drives it through the full Software Development Lifecycle — requirements, architecture, implementation, testing, and a GitHub PR — entirely via specialist AI agents. You write the user story; the pipeline writes the code.

---

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd automated-documentation-sync
   ```

2. **Write your user story** — create `user-stories/user-story-1.md` describing what you want to build (see `user-stories/user-story-template.md` for format)

3. **Invoke the orchestrator** in Claude Code:
   ```
   @orchestrator process user-stories/user-story-1.md
   ```

4. **Follow the prompts** — answer the Requirements and Architecture agents' questions, approve each step with `y`, and confirm the PR at the end

---

## Pipeline Architecture

```
user-stories/user-story-N.md
        │
        ▼
[ORCHESTRATOR]
        │
        ├─[L1]─► Requirements Agent ──► docs/requirements.md
        │
        ├─[L1]─► Architecture Agent ──► docs/architecture.md
        │
        ├─[L2]─► Design Review Agent ──► docs/design-review.md
        │
        ├─[L2]─► Impl Planner Agent ──► docs/impl-plan.md
        │
        ├─[L2]─► Implementation Agent ──► src/ + tests/
        │
        ├─[L2]─► Doc Sync Agent ──► docs/ (updated)
        │
        ├─[L2]─► Code Review Agent ──► output/reports/code-review.md
        │
        ├─[L2]─► Verification Agent ──► output/test-results/results.md
        │
        └─[L3]─► PR Agent ──► GitHub Pull Request
```

---

## Folder Structure

```
automated-documentation-sync/
├── .claude/
│   ├── agents/             # Specialist agent definitions (9 agents + orchestrator)
│   ├── skills/             # Reusable skill files invoked by agents
│   └── settings.json       # Hooks configuration
├── user-stories/           # Your input: one .md file per story
├── docs/                   # Generated: requirements, architecture, plan, changelog
├── src/                    # Generated: Python source code
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── output/
│   ├── reports/            # Code review output
│   └── test-results/       # Verification output
├── CLAUDE.md               # Pipeline instructions for Claude Code
├── pyproject.toml
└── README.md
```

---

## Agent Reference

| Agent | Role | Interaction Level |
|---|---|---|
| orchestrator | Entry point; sequences all other agents | — |
| requirements | Elicits and documents requirements from user story | L1 — Interactive |
| architecture | Proposes system design based on requirements | L1 — Interactive |
| design-review | Reviews architecture for risks and gaps | L2 — Run + Approve |
| implementation-planner | Breaks work into ordered tasks | L2 — Run + Approve |
| implementation | Writes Python source code and tests | L2 — Run + Approve |
| documentation-sync | Keeps docs in sync with actual code | L2 — Run + Approve |
| code-review | Reviews code for correctness and quality | L2 — Run + Approve |
| verification | Runs tests and enforces quality gates | L2 — Run + Approve |
| pr | Drafts and creates GitHub Pull Request | L3 — Explicit Approve |

---

## Requirements

- **Claude Code** CLI (latest version)
- **Python** 3.11 or higher
- **Git** installed and configured
- **GitHub CLI** (`gh`) for PR creation

---

## Contributing

### Adding a new agent
1. Create `.claude/agents/<agent-name>.md` following the existing agent format (frontmatter + system prompt + I/O contract)
2. Add the agent as a step in `.claude/agents/orchestrator.md`
3. Add any new output paths to `CLAUDE.md` under File Conventions

### Adding a new skill
1. Create `.claude/skills/<skill-name>.md` with the structured template
2. Reference it from the relevant agent's system prompt with `Invoke the <skill-name> skill`
