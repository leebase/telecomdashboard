# telecomdashboard Project Plan

> Strategic roadmap for reviving and maintaining the existing telecom KPI dashboard, with a phased path for the parked agent prototype.

For current execution, see `sprint-plan.md`.

---

## Project Overview

`telecomdashboard` is a Streamlit-based telecom KPI dashboard backed by SQLite/CSV data, with AI-assisted insights, theme support, benchmarking, health checks, security controls, and a sizeable automated test suite.

This project is not starting from zero. The current mission is to restore confidence, documentation accuracy, and maintainability around a codebase that already has substantial feature work.

The repo also contains a separate multi-agent playbook prioritization prototype. That capability now looks worth pursuing, but only through staged validation so the main dashboard does not lose quality.

---

## Objectives

### Primary Objective

Restore the project to a runnable, understandable state so the dashboard can be iterated on confidently.

### Secondary Objectives

- Align setup docs and metadata with the real runtime
- Re-validate core workflows, data loading, and tests
- Reintroduce the separate multi-agent prototype only when its business value, trust model, and operating boundary are clear

---

## Constraints

- Avoid breaking the existing dashboard while reviving the project
- Do not add runtime dependencies without explicit approval
- Preserve local data, configuration, and historical docs unless there is a clear reason to change them
- Distinguish between verified current behavior and historically documented behavior

---

## Development Phases

### Phase 1 — Historical Foundation

**Status**: Complete before AgentFlow adoption

**Delivered**:
- Streamlit dashboard and KPI visualizations
- CSV and SQLite data warehouse
- Theme system and print support

### Phase 2 — Historical Hardening and Intelligence

**Status**: Complete before AgentFlow adoption

**Delivered**:
- AI insights workflow and LLM integration
- Security protections and security-focused tests
- Health checks, logging, feature flags, and config tooling
- Expanded integration, performance, and reliability test coverage

### Phase 3 — Revival and Stabilization

**Status**: Active

**Goals**:
- Reconcile documentation with reality
- Restore the development/runtime environment
- Smoke test the main dashboard
- Resolve setup and packaging drift

**Success Criteria**:
- A documented setup path launches `app.py`
- Core validation commands run cleanly in the local environment
- AgentFlow docs match the current repo

### Phase 4 — Modernization

**Status**: Next

**Candidate work**:
- Clean up package metadata and dependency sources
- Rationalize legacy versus active modules
- Introduce CI or reproducible local validation scripts if missing

### Phase 5 — Directional Decisions

**Status**: Replaced by phased prototype pursuit

This repo has now moved past the binary question of "keep or kill" for the prototype. The better path is phased pursuit.

### Phase 5 — Agent Discovery And Product Framing

**Status**: Next candidate phase

**Goals**:
- Define the business job of the playbook-prioritization prototype precisely
- Decide who the user is: operator, consultant, executive reviewer, or internal strategy team
- Identify the minimum inputs required to generate trustworthy plays
- Separate recommendation logic from UI polish and demo theatrics

**Success Criteria**:
- A crisp problem statement exists for the agent system
- The prototype is described as a recommendation workflow, not generic "agent orchestration"
- A first trusted output contract exists for generated plays and portfolio recommendations

### Phase 6 — Agent Input And Scoring Hardening

**Status**: Planned

**Goals**:
- Replace purely theatrical/demo assumptions with explicit scoring logic
- Trace play recommendations back to source KPI or business signals
- Define ranking, ROI, effort, and risk semantics so they are reviewable
- Add focused tests around play generation and portfolio scoring

**Success Criteria**:
- A user can inspect why a play was recommended
- Portfolio outputs have stable schemas and deterministic scoring rules where possible
- Agent tests validate recommendation structure and scoring behavior

### Phase 7 — Workflow Validation And Internal Pilot

**Status**: Planned

**Goals**:
- Run the prototype as a bounded internal strategy-support workflow
- Validate whether the output is useful enough to influence prioritization decisions
- Decide whether the prototype remains separate or becomes a supported product surface

**Success Criteria**:
- At least one internal use case or demo flow is credible end to end
- The team decides whether to keep, integrate, or archive the prototype based on evidence

---

## Success Metrics

- `streamlit run app.py` works from a documented environment
- Local data bootstrap and config validation are repeatable
- Tests run from the restored environment with actionable failures only
- New contributors can identify the primary app, setup path, and current roadmap within a few minutes
- If the agent prototype re-enters scope, its recommendations can be explained, validated, and tied to a concrete user decision process

---

## Current Status

| Field | Value |
|-------|-------|
| Active Phase | Phase 3 — Revival and Stabilization |
| Mode | 2 (Collaborative) |
| Next Milestone | Complete the revival sprint, then start Phase 5 agent discovery with a bounded sprint |

---

## Guiding Principle

Preserve the working product, reduce ambiguity, and only expand scope when the next layer has a clear user, a clear decision value, and a defensible quality bar.
