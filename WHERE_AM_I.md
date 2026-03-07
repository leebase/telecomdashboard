# WHERE_AM_I — telecomdashboard

> Product-level orientation. For session detail, read `context.md`.

---

## Project Health

| Attribute | Value |
|-----------|-------|
| Project | telecomdashboard |
| Current Phase | Revival Sprint |
| Overall Status | 🟡 Existing product, validated local environment, with the main dashboard now rechecked through both the real user path and a real browser render, and a phased plan defined for the parked agent prototype |
| Last Updated | 2026-03-07 |

---

## Progress Against Product Goals

### Product Goals

| Goal | Status | Notes |
|------|--------|-------|
| Deliver a telecom KPI dashboard across five business pillars | ✅ Largely implemented | Main Streamlit app and supporting modules already exist |
| Support AI-assisted analysis and benchmark context | ✅ Implemented historically | Requires valid configuration and API key to verify now |
| Operate with enterprise-style config, security, logging, and health features | ✅ Locally revalidated | Maintained config, AI, security, integration, and performance tests now pass, validator/health tooling runs, and a health CLI is available |
| Make the project easy to restart and maintain | ⏳ In progress | AgentFlow docs are aligned, setup is reproducible, strict validation is clean, core operational commands are stronger, and naming now matches the user's broader project conventions |

### Current Revival Goals

| Goal | Status | Notes |
|------|--------|-------|
| Re-baseline AgentFlow docs to the existing codebase | ✅ Done | Core state files now describe the real project |
| Restore a runnable local environment | ✅ Done | Core runtime and optional enterprise test dependencies are installed and documented |
| Verify the main dashboard end to end | ✅ Done for local revival scope | `streamlit run app.py` starts, full dashboard render smoke testing passes, the repo config remains stable after test runs, and browser rendering no longer blanks the first screen |
| Clarify scope of the multi-agent prototype | ✅ Done for this sprint | Prototype is parked for the revival sprint and now has a phased re-entry plan |

---

## Sprint Position

| Sprint | Focus | Status |
|--------|-------|--------|
| Revival Sprint | Documentation alignment, environment restore, validation, cleanup | 🟡 Active |

---

## Product Risks and Blockers

| Risk or Blocker | Impact | Status |
|-----------------|--------|--------|
| Coverage-heavy default pytest output | Slower and noisier, but intentionally retained during the quality-first revival pass | 🟡 Active |
| `README.md` and `pyproject.toml` still contain scaffold-era metadata | Reduced but not fully eliminated documentation/setup drift | 🟡 Mitigated |
| Multiple entry points create scope ambiguity | Revival work may drift between two different apps | 🟡 Active |
| AI features depend on local secrets and external API availability | Insight flows may fail even after the app boots | 🟡 Active |
| Production readiness still depends on missing env config | Validator correctly reports missing `ENVIRONMENT`, `LLM_API_KEY`, `DATABASE_URL`, `LOG_LEVEL`, and production logging posture | 🟡 Active |
| Schema/config drift can reappear in the dashboard UI if tests and runtime are not validated together | Mitigated by the new app smoke test and by isolating config-manager tests from the live repo config | 🟡 Mitigated |

---

## Key Decisions Made

| Decision | Rationale | Date |
|----------|-----------|------|
| Main dashboard is the default product surface | It has the strongest evidence of completed feature work and documentation | 2026-03-07 |
| AgentFlow should describe current reality, not a clean-slate roadmap | The repository already contains substantial implementation history | 2026-03-07 |
| Agent prototype is parked for this sprint | The current goal is a high-quality main dashboard release rather than concurrent stabilization of two apps | 2026-03-07 |
| Agent prototype should return through phased discovery, not full parallel revival | Its likely value is recommendation support, but that needs a user/job/output definition before broader investment | 2026-03-07 |

---

## What Done Looks Like For Revival

- Main dashboard starts from a documented local setup
- Core dashboard tabs render against the local data store
- Validation commands and tests run in a restored environment
- AgentFlow docs, README, and dependency metadata no longer contradict the codebase
- The role of the multi-agent prototype is explicitly decided

---

This file is the compass. If it reads like a greenfield project again, it is wrong.
