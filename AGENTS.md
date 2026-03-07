# Agent Guide: telecomdashboard

> For AI agents working on the telecomdashboard project.
>
> This repository adopted AgentFlow after substantial code already existed. Do not assume the project is new just because the AgentFlow files are recent.

---

## Startup Protocol

At the start of every session, in order:

1. Read `AGENTS.md`
2. Read `context.md`
3. Read `WHERE_AM_I.md`
4. Read `result-review.md`
5. Read `sprint-plan.md`

If the task touches product direction or architecture, also read `product-definition.md` (or the compatibility alias `project-definition.md`) and `architecture.md`.

---

## Project Reality

The primary product in this repo is a Python/Streamlit telecom KPI dashboard.

Key entry points and areas:
- `app.py` is the main dashboard application.
- `data/` contains the SQLite database and CSV warehouse inputs.
- `database_connection.py`, `config_manager.py`, `health_check.py`, `security_manager.py`, and `llm_service.py` support the operational feature set.
- `tests/` contains security, AI safety, performance, integration, config, and unit tests.
- `runAgentsApp.py`, `agents/`, and `models/play_models.py` are a separate multi-agent prototype. Treat them as secondary until the human confirms they are part of the revival scope.

The scaffolded package entry point in `src/telecomdashboard/main.py` is not the primary runtime for this project.

### Repo Layout

- `app.py`: primary dashboard entry point
- `runAgentsApp.py`: separate Streamlit prototype for agent orchestration
- `agents/`, `models/`: agent prototype internals
- `src/`: partial package-style refactor and scaffold leftovers
- `data/`: SQLite database, CSVs, schema, and data catalog
- `docs/`: historical architecture, deployment, API, and feature docs
- `styles/`: theme assets
- `tests/`: automated validation suites

---

## Available Skills

Load the relevant skill file when the trigger applies.

| Trigger | Skill to Load |
|---------|---------------|
| You are implementing a feature or fix | `skills/development-loop.md` |
| You are about to test your work | `skills/test-as-lee.md` |
| You are about to commit | `skills/documentation.md` |
| You are creating a backlog item | `skills/backlog.md` |
| You are closing a sprint or preparing a release | `skills/code-review.md` |

### Test As Lee Acceptance Bar

For any change that affects the main dashboard UI, startup path, theme layer, config path, or first-run experience, do not claim success until the real entry point is validated at the browser level.

Minimum acceptance:
- Launch `streamlit run app.py`
- Confirm the first screen is visibly populated, not just free of Python exceptions
- Verify the main title/tabs/KPI region are present in a browser render, not only via `AppTest`
- Treat a blank, hidden, or obviously malformed first screen as a failed test even if pytest is green

`streamlit.testing.v1.AppTest` is useful but insufficient on its own for CSS/DOM visibility regressions.

---

## Task Rehydration

Before continuing any task mid-session:

1. Re-read `sprint-plan.md`
2. Re-read any files you changed earlier in the session
3. Re-check the current objective in `context.md`
4. Confirm whether the task is for the main dashboard or the separate agent prototype

---

## Autonomy Modes

The `Mode` field in `context.md` controls how independently you work:

| Mode | Name | Behavior |
|------|------|----------|
| 1 | Supervised | Ask before every significant action |
| 2 | Collaborative | Implement routinely, ask on material decisions |
| 3 | Autonomous | Execute independently within guardrails |

Default is Mode 2 unless `context.md` says otherwise.

---

## Guardrails

### Allowed

- Modify code and docs inside this repository
- Add tests for changed behavior
- Update AgentFlow memory files at the end of the session
- Create backlog items in `backlog/candidates/`
- Reconcile stale project documentation with the actual codebase

### Not Allowed Without Explicit Permission

- Add external runtime dependencies
- Make breaking changes to current dashboard behavior
- Delete files just because they look old
- Assume the multi-agent prototype is abandoned and remove it
- Commit directly to protected branches
- Skip documenting important discoveries about project drift

---

## Documentation Map

| File | Purpose |
|------|---------|
| `context.md` | Session state and immediate next actions |
| `WHERE_AM_I.md` | Product-level progress and risks |
| `result-review.md` | Running log of completed work and historical milestones |
| `sprint-plan.md` | Current tactical sprint |
| `project-plan.md` | Revival roadmap and medium-term priorities |
| `product-definition.md` | Product goals and scope boundaries |
| `project-definition.md` | Compatibility alias for product scope used by other AgentFlow repos |
| `architecture.md` | Current technical architecture and known drift |
| `feedback.md` | Review findings and follow-up items |
| `sprint-review.md` | External sprint assessment |

For deeper legacy detail, use the docs already in `docs/`, especially `docs/appArchitecture.md`, `docs/api.md`, `docs/deployment.md`, and `docs/CONFIGURATION_GUIDE.md`.

---

## Communication Style

- Be concise
- Use concrete file paths and commands
- Distinguish facts from assumptions
- Call out repo drift immediately
- Prefer preserving working behavior over neatness

---

## Practical Commands

Use the real project entry points and validation commands:

- Install runtime deps: `pip install -r requirements.txt`
- Run main app: `streamlit run app.py`
- Run agent prototype: `streamlit run runAgentsApp.py`
- Load local data: `python load_csv_data.py`
- Run tests: `pytest tests/ -v`

Treat `Makefile` as helpful but not authoritative until the dependency/setup drift is cleaned up. It currently references `requirements-dev.txt`, which is missing.

---

## Session End Requirement

Before ending a work session:

1. Update `context.md`
2. Update `result-review.md`
3. Update `sprint-plan.md` if task status changed
4. Update `WHERE_AM_I.md` if project posture or risks changed

Treat these updates as part of the work, not optional cleanup.
