# telecomdashboard Session Context

> Working memory for session continuity.

---

## Snapshot

| Attribute | Value |
|-----------|-------|
| Phase | Revival and stabilization |
| Mode | 2 (Collaborative) |
| Last Updated | 2026-03-07 |
| Primary Runtime | `streamlit run app.py` |
| Secondary Runtime | `streamlit run runAgentsApp.py` |

### Current Status

| Area | Status | Notes |
|------|--------|-------|
| Main dashboard codebase | Existing and feature-rich | Telecom KPI dashboard with AI insights, theming, config, health, and security layers |
| AgentFlow docs | Re-baselined | Placeholder scaffold text replaced with project-specific state |
| Local environment | Restored and validated | Rebuilt `venv`, aligned dependency metadata, added optional enterprise test dependencies, and re-verified startup and test paths |
| Product scope | Clarified for this sprint | Main dashboard is the active revival product; the agent prototype is explicitly parked as secondary work |
| Lee-style validation | Re-run and corrected | Dashboard render path now verified against the real local DB and tests no longer mutate the live config |

---

## What's Happening Now

### Current Work Stream
Reviving the older project with the main dashboard held to a "test as Lee" acceptance bar: the same entry point the user runs must work after the full local validation cycle.

### Recently Completed
- AgentFlow baseline reviewed against the real repository
- Missing `sprint-plan.md` identified and created
- Project status reframed from "new scaffold" to "existing dashboard in revival"
- Broken virtualenv replaced and required Python packages installed
- First blocker-fix pass executed from the formal code review
- Maintained `tests/` suite brought back to green, including config, unit, AI, security, integration, and performance buckets
- `pytest tests -q -x` and `pytest -q -x` both complete successfully in the restored environment
- Configuration validator and health-check tooling revalidated against the live codebase
- Main dashboard warning cleanup completed: deprecated Streamlit sizing calls removed from the primary app path, SQLite connection lifecycle fixed, and flaky cache timing in the database unit suite stabilized
- Strict warning enforcement now passes on the maintained suite, including Python 3.13 SQLite date-adapter deprecations and Snowflake adapter warning cleanup
- First-class health CLI added to the installed helper command, with JSON output on stdout and log noise routed to stderr for automation safety
- Added `project-definition.md` as a compatibility alias for repos and workflows that expect that filename
- Fixed dashboard runtime drift found during real-user retesting: `config/config.yaml` is back on `data/telecom_db.sqlite`, Customer Experience charts now use the actual DB columns, and `tests/unit/test_config_manager.py` no longer rewrites the live repo config during test runs
- Added an app-level smoke test in `tests/integration/test_app_smoke.py` so full dashboard rendering is part of the maintained validation path
- Fixed a browser-visible blank-screen regression in the theme layer by removing the CSS rule that hid `.stApp > div:first-child` in both shipped themes

### In Progress
- Quality-first follow-up on remaining repo/product polish now that the main validation path and real-user dashboard render path are green
- Planning the phased reintroduction of the parked agent prototype as a bounded discovery effort

---

## Decisions Locked

| Decision | Rationale | Date |
|----------|-----------|------|
| Treat `app.py` as the primary product entry point | It matches the historical README, docs, changelog, and surrounding modules | 2026-03-07 |
| Park `runAgentsApp.py` and `agents/` for this revival sprint | Quality-first focus is on shipping a stable main dashboard before broadening scope again | 2026-03-07 |
| Do not claim the project is green until dependencies are restored and smoke tests run | This prevented premature success claims during the revival pass | 2026-03-07 |
| Pin Pydantic to v1 for now | Existing models rely on v1 validator behavior and fail under v2 | 2026-03-07 |
| Treat legacy `test_phase*.py` files as demo/prototype scripts, not maintained pytest modules | They are script-style artifacts and distort the default pytest signal | 2026-03-07 |
| Keep enterprise adapter dependencies as optional dev/enterprise installs | They are required for adapter validation but not for the main Streamlit dashboard runtime | 2026-03-07 |
| Keep coverage and warning enforcement in the default validation path during revival | The current priority is product quality and regression visibility over shorter local test output | 2026-03-07 |
| Treat `requirements*.txt` as the canonical dependency source during revival | It matches the documented install flow and the repo still relies on top-level modules outside the `src/` package boundary | 2026-03-07 |
| Treat `streamlit run app.py` plus a full render check as the acceptance bar for dashboard work | Green unit/integration tests are not enough if the live user path still fails on config or schema drift | 2026-03-07 |
| Browser-level first-screen validation is required for dashboard/theme changes | Internal Streamlit tests do not catch CSS rules that can hide the visible app | 2026-03-07 |

---

## Open Questions

1. Should the lightweight scaffold package in `src/telecomdashboard/` be expanded, replaced, or removed later?
2. When should the parked multi-agent prototype be brought back into active scope, if at all?

---

## Next Actions Queue

| Rank | Action | Owner | Done When |
|------|--------|-------|-----------|
| 1 | Start the proposed Agent Discovery Sprint | Human or AI | A concrete business-purpose and output-contract review is underway for the prototype |
| 2 | Review whether the helper CLI should absorb more operational commands beyond `health` | Human or AI | There is a clear boundary for what belongs in `telecomdashboard` versus top-level scripts |
| 3 | Decide the longer-term role of `pyproject.toml` beyond packaging metadata and extras | Human or AI | The repo either continues with requirements-led installs or completes a fuller package-style refactor |

---

## Working Conventions

### Start of session
1. Read `AGENTS.md`
2. Read this file
3. Read `WHERE_AM_I.md`, `result-review.md`, and `sprint-plan.md`
4. Reconfirm whether the task is for the dashboard or the agent prototype

### End of work unit
1. Update this file if status changed
2. Move completed work into `result-review.md`
3. Adjust `sprint-plan.md`
4. Keep open questions short and actionable

---

## Environment Notes

- Working directory: `/Users/leeharrington/projects/telecomdashboard`
- Primary stack: Python, Streamlit, Pandas, Altair, SQLite
- AI integration: OpenRouter-backed insights flow via `llm_service.py`
- Data dependency: local SQLite database and CSV warehouse files in `data/`

---

This file should describe the real project state, not the idealized future state.
