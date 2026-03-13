# Agent Guide: telecom-metadata

> For AI agents working on the telecom-metadata project.
>
> This repository is not a clean-slate metadata engine. It is a working fork of
> the telecom dashboard with an in-progress metadata runtime layered into it.

---

## Startup Protocol

At the start of every session, in order:

1. Read `AGENTS.md`
2. Read `context.md`
3. Read `WHERE_AM_I.md`
4. Read `result-review.md`
5. Read `sprint-plan.md`

If the task touches product direction or architecture, also read
`product-definition.md` (or the compatibility alias `project-definition.md`) and
`architecture.md`.

---

## Project Reality

The primary goal in this repo is not to maintain the legacy telecom dashboard as
the end product. The active goal is to prove that a metadata-driven runtime can
recreate that dashboard faithfully enough to support later generalization.

Key entry points and areas:
- `app.py` is still the main Streamlit entry point and contains the legacy
  dashboard plus the metadata feature flag path.
- `src/metadata_runtime/` contains metadata models, loader, dialect support,
  and CLI wiring.
- `src/ui/`, `src/data/`, and `apps/meta/` contain the metadata rendering,
  widget, query, and provider layers.
- `metadata/dashboard_telco.yaml` is the canonical telco proof pack.
- `tools/generate_telco_metadata.py` is the current generator stub.
- `tests/metadata/`, `tests/ui/`, `tests/data/`, and `tests/visual/` cover the
  metadata runtime and its proof surface.

The legacy telecom dashboard remains the source-of-truth target. The metadata
runtime is the product under construction.

### Repo Layout

- `app.py`: legacy dashboard runtime plus `USE_METADATA` switch
- `apps/meta/app.py`: metadata-only Streamlit entry point
- `src/metadata_runtime/`: metadata schema, loader, dialects, and CLI
- `src/ui/`: layout engine, metadata app renderer, widget registry, parity code
- `src/data/`: datasource abstraction, query compiler, cache, metadata provider
- `metadata/`: metadata packs, including `dashboard_telco.yaml`
- `tools/`: metadata generation and proof-support tooling
- `tests/`: maintained automated validation suites

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

If the local `skills/` files are missing, continue with the same workflow
intent rather than inventing replacements.

### Metadata Proof Acceptance Bar

For any change that affects the metadata runtime, metadata schema, proof pack,
or verification harness, do not claim success until the metadata path is
validated at the real app level.

Minimum acceptance:
- Validate the canonical pack with `python -m metadata_cli validate metadata/dashboard_telco.yaml`
- Launch the metadata path with `USE_METADATA=true streamlit run app.py` or
  `streamlit run apps/meta/app.py`
- Confirm the first screen is visibly populated, not just free of Python exceptions
- Verify the intended tabs and primary KPI region are present in a browser render
- Treat placeholder widgets, blank sections, or a generic shell that omits the
  target dashboard contract as a failed proof even if pytest is green

`streamlit.testing.v1.AppTest` is useful but insufficient on its own for
browser-visible parity regressions.

---

## Task Rehydration

Before continuing any task mid-session:

1. Re-read `sprint-plan.md`
2. Re-read any files you changed earlier in the session
3. Re-check the current objective in `context.md`
4. Confirm whether the task is about legacy dashboard behavior, metadata mode,
   or proof/verification tooling

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
- Reconcile stale metadata-runtime documentation with the actual codebase

### Not Allowed Without Explicit Permission

- Add external runtime dependencies
- Claim cross-industry support before telco parity is actually verified
- Delete legacy dashboard files just because the metadata runtime exists
- Hide proof gaps behind mocked tests or doc wording
- Commit directly to protected branches
- Skip documenting project drift between the design docs and the real runtime

---

## Documentation Map

| File | Purpose |
|------|---------|
| `context.md` | Session state and immediate next actions |
| `WHERE_AM_I.md` | Product-level progress and risks |
| `result-review.md` | Running log of completed work and historical milestones |
| `sprint-plan.md` | Current tactical sprint |
| `project-plan.md` | Medium-term roadmap for parity and generalization |
| `project-description.md` | Repo-facing overview of purpose and status |
| `product-definition.md` | Product goals and scope boundaries |
| `project-definition.md` | Compatibility alias for product scope |
| `design.md` | Intended metadata-runtime system design |
| `architecture.md` | Current technical architecture and known drift |
| `feedback.md` | Review findings and follow-up items |
| `sprint-review.md` | External or end-of-sprint assessment |

For deeper legacy detail, use the docs in `docs/`, especially
`docs/refactor/ARCHITECTURE.md`, `docs/refactor/SCHEMA.md`,
`docs/refactor/REFACTOR_PLAN.md`, and the source-dashboard screen contract in
`/Users/leeharrington/projects/telecomdashboard/docs/METADATA_DRIVEN_SCREEN_SPEC.md`.

---

## Communication Style

- Be concise
- Use concrete file paths and commands
- Distinguish facts from assumptions
- Call out repo drift immediately
- Prefer verifiable behavior over aspirational wording

---

## Practical Commands

Use the real project entry points and proof commands:

- Install runtime deps: `pip install -r requirements.txt`
- Validate metadata pack: `python -m metadata_cli validate metadata/dashboard_telco.yaml`
- Run legacy/default app path: `streamlit run app.py`
- Run metadata mode through the main entry point: `USE_METADATA=true streamlit run app.py`
- Run metadata-only app: `streamlit run apps/meta/app.py`
- Load local data: `python load_csv_data.py`
- Run tests: `pytest tests/ -v`

Treat `Makefile` as helpful but not authoritative until dependency and proof
tooling drift is cleaned up.

---

## Session End Requirement

Before ending a work session:

1. Update `context.md`
2. Update `result-review.md`
3. Update `sprint-plan.md` if task status changed
4. Update `WHERE_AM_I.md` if project posture or risks changed

Treat these updates as part of the work, not optional cleanup.
