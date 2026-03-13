# telecom-metadata Session Context

> Working memory for session continuity.

---

## Snapshot

| Attribute | Value |
|-----------|-------|
| Phase | Metadata-runtime parity and proof |
| Mode | 2 (Collaborative) |
| Last Updated | 2026-03-12 |
| Primary Runtime | `USE_METADATA=true streamlit run app.py` |
| Secondary Runtime | `streamlit run apps/meta/app.py` |

### Current Status

| Area | Status | Notes |
|------|--------|-------|
| Legacy dashboard baseline | Present | The repo still contains a runnable telco dashboard fork in `app.py` |
| Metadata runtime code | Partially implemented, boot restored | Loader, models, compiler, provider, layout, widget, and runtime switch paths exist; metadata mode now shares the legacy shell, resolves pack-defined chart/widget overrides, and renders the benchmark tab through metadata-owned widgets |
| AgentFlow docs | Re-baselined | Session-state and project-definition docs now exist and describe the metadata project |
| Proof harness | Real and green in the local proof baseline | Structural/data parity is automated and browser-real screenshot checks now pass across all six tabs |
| Product claim | Narrow local proof achieved | The repo can now make a bounded local claim that the telco dashboard can be reproduced through the metadata entry path in the pinned local environment |

---

## What's Happening Now

### Current Work Stream

Turning the forked telco dashboard into a metadata-first proof repo that can
recreate the source dashboard intentionally, then verify that claim with real
automation and browser checks.

### Recently Completed

- Added a repo-owned post-run enforcement script at
  `connie-book/scripts/enforce-after-run.sh` and wired
  `connie-book/WORKFLOW.md` to call it from the Symphony `after_run` hook
- Replaced the telco pack generator stub with a deterministic normalization
  step in `tools/generate_telco_metadata.py`, added focused tests in
  `tests/unit/test_generate_telco_metadata.py`, and regenerated
  `metadata/dashboard_telco_generated.yaml` with stable provenance metadata
- Validated the new Connie Book completion guard with a controlled replay:
  forcing `CON-6` back to `Done` now reopens it to `Todo` automatically and
  leaves a Linear comment when
  `connie-book/AI_TOOL_ONBOARDING_GUIDE.md` is still missing
- Restarted the upstream Symphony daemon through `zsh -lic` so it inherits the
  real `LINEAR_API_KEY` environment again; `CON-6` is now claimed under the
  corrected workflow
- Reopened Connie Book Linear issue `CON-6` after the live Symphony run moved
  it to `Done` without leaving `AI_TOOL_ONBOARDING_GUIDE.md` in the live
  `connie-book/` source tree
- Tightened the Connie Book workflow and backlog so `CBOOK-008` now has an
  explicit artifact path and no future `Done` transition is valid without a
  concrete live-tree file check after sync
- Repaired the moved `telecom-metadata` git worktree with
  `git worktree repair /Users/leeharrington/projects/telecom-metadata` from the
  parent `telecomdashboard` repo so repo-backed Symphony workspaces can start
  cleanly again
- Reworked `connie-book/WORKFLOW.md` workspace hooks to use a real repo clone
  inside each issue workspace, overlay the current live working tree before
  each run, and sync the `connie-book/` subtree back into the live repo after
  each run
- Verified that the live Linear-backed Symphony service now gets past the
  earlier workspace safety failures and starts a real `CON-6` Codex session in
  a repo-backed workspace rooted under
  `~/code/symphony-workspaces/connie-book/CON-6`
- Upgraded local `codex` from `0.46.0` to `0.113.0` and aligned the Connie Book
  workflow to the upstream Symphony-style app-server command
- Wired the real Connie Book Linear project slug into
  `connie-book/WORKFLOW.md` using the full project URL slug
- Added `CBOOK-014 Replace Linear with a project-owned tracker adapter` to the
  `connie-book/` backlog so the project records the intent to reduce Linear
  lock-in while staying aligned with upstream Symphony
- Cloned `openai/symphony` into `connie-book/symphony-reference` for direct
  upstream use rather than spec-only reference
- Installed the local Symphony runtime prerequisites on this machine:
  `mise`, `erlang`, and `elixir`
- Built the reference implementation successfully in
  `connie-book/symphony-reference/elixir` and verified the generated
  `bin/symphony` entrypoint is runnable
- Bootstrapped a new repo-local planning workspace in `connie-book/` for a
  daughter-first book-writing and AI-learning program that doubles as a
  Symphony orchestration training ground
- Added the initial `connie-book/` source-of-truth artifacts:
  - `PROJECT_BRIEF.md`
  - `ROADMAP.md`
  - `LESSON_PLAN.md`
  - `BACKLOG.md`
  - `WORKFLOW.md`
  - `RUN_LOG.md`
  - `agents/` mission files
- Seeded the workspace with a 12-week lesson plan, issue-like backlog,
  Symphony-compatible workflow contract, and simulated run log entries so the
  hourly operating model is explicit from day one
- Added `connie-book/HOURLY_ORCHESTRATION.md` and `connie-book/SYMPHONY_SETUP.md`
  so the project now has an explicit live-run model: repo-local hourly
  automation now, tracker-backed Symphony later
- Promoted the hourly automation item into the active queue and added an
  explicit workflow-improvement loop so the agent team is expected to refine its
  own missions, handoffs, and backlog rules over time
- Documented the new workspace as intentionally repo-local and separate from the
  telco proof claim so the project does not accidentally overstate product
  scope
- Replaced the generic repository guide with an AgentFlow-oriented `AGENTS.md`
- Added the missing session-state files: `context.md`, `WHERE_AM_I.md`,
  `result-review.md`, `sprint-plan.md`, `product-definition.md`,
  `project-definition.md`, and `architecture.md`
- Added metadata-specific `project-description.md`, `design.md`, and
  `project-plan.md`
- Reframed the repo docs around the actual current state: metadata runtime
  exists, proof is incomplete, and the source dashboard remains the parity target
- Expanded `sprint-plan.md` into a concrete remediation plan with ordered
  workstreams for boot repair, shell/widget parity, and proof automation
- Restored metadata-runtime boot compatibility with the pinned Pydantic version
- Repaired SQLite datasource error propagation so failed metadata queries can
  fall back cleanly
- Fixed stale or invalid SQLite view definitions and rebuilt views in
  `data/telecom_db.sqlite`
- Fixed parity utility bugs in `src/ui/visual_parity.py`
- Added a local `snowflake` test stub so Snowflake unit tests can patch their
  target without the optional connector installed
- Revalidated the metadata proof baseline:
  - `python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
  - `pytest tests/metadata tests/data tests/ui -q` passes with 72 passing tests
  - `USE_METADATA=true streamlit run app.py --server.headless true --server.port 8515` starts successfully
- Connected `metadata.widgets` chart and widget overrides into the runtime
  resolver so the canonical telco layout can resolve standalone chart/table/form
  entries instead of dropping them immediately to placeholders
- Added dataset-backed payload assembly for pack-defined widget overrides and
  extended the widget registry with the telco pack’s remaining chart types:
  `stacked_bar`, `multi_series_line`, `forecast_band`, and `heatmap`
- Fixed `QueryCompiler` compatibility for auxiliary metrics now that
  pack-defined widgets can reference them directly
- Verified the new path with focused tests plus pack validation:
  - `pytest tests/data/test_metadata_provider.py tests/data/test_query_compiler.py tests/ui/test_widget_registry.py tests/ui/test_metadata_runtime_app.py -q` passes with 12 tests
  - `pytest tests/metadata tests/data tests/ui -q` passes with 78 passing tests and 2 skips
  - `python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
  - `USE_METADATA=true streamlit run app.py --server.headless true --server.port 8516` starts successfully
- Reused the legacy theme/sidebar/page-header shell in metadata mode and added
  matching time-period controls so legacy and metadata paths now expose the same
  high-level shell structure under `AppTest`
- Fixed stale legacy SQLite queries in `database_connection.py` so the legacy
  app path renders cleanly against the rebuilt proof database again
- Added structural and data parity tests between legacy and metadata paths:
  - `tests/ui/test_app_parity.py`
  - `tests/data/test_legacy_metadata_parity.py`
- Replaced synthetic visual proof with a real local-browser harness in
  `src/ui/visual_parity.py` using headless Chrome DevTools screenshots plus PIL
  pixel diffs against the source screenshot set
- Reworked `tests/visual/test_visual_parity.py` into an opt-in browser-real
  parity suite against `/Users/leeharrington/projects/telecomdashboard/docs/screen-grabs/current-look`
- Fixed cache persistence serialization/cleanup drift in `src/data/cache.py`
- Corrected `pytest.ini` so pytest actually loads the repo config, registers the
  `integration` and `visual` markers, and no longer depends on the missing
  `pytest-cov` plugin for local proof runs
- Hardened the visual proof harness so background-only browser captures fail
  immediately instead of slipping under the pixel-diff tolerance
- Installed `playwright` plus local Chromium in `.venv` so the next browser
  proof iteration can switch off the broken Chrome CDP capture path without
  adding more environment setup
- Fixed the browser-visible blank-screen regression in the active themes by
  removing CSS that hid `.stApp > div:first-child` in current Streamlit builds
- Switched the browser proof path to Playwright-driven screenshots with a
  less brittle DOM readiness check
- Replaced deprecated `use_container_width` calls in the metadata parity path
  and related dashboard surfaces with the current `width` API where supported
- Removed the benchmark-management runtime bypass so the benchmark tab now
  renders through the metadata pack’s table/history/editor widgets
- Defined the explicit telco proof gate in `sprint-plan.md`
- Verified the current proof state:
  - `pytest tests/metadata tests/data tests/ui -q` passes with 86 passing tests and 2 skips
  - `pytest tests/visual/test_visual_parity.py -q -m visual` passes across all 6 tabs
  - `python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
  - A real `USE_METADATA=true streamlit run app.py` boot no longer emits the
    prior `use_container_width` deprecation warnings during page render

### In Progress

- Wiring the built Symphony reference implementation to a real tracker-backed
  workflow for `connie-book/`; the real service is now running against Linear,
  the false-close path is guarded by executable post-run enforcement, and the
  remaining runtime gap is one clean `CON-6` artifact-producing run that leaves
  `AI_TOOL_ONBOARDING_GUIDE.md` in the live source tree without the guard
  needing to intervene
- Hardening the telco pack generator beyond deterministic normalization so it
  can evolve from stable rewrite into true legacy-aware extraction or mapping
- Deciding when the telco proof is strong enough to start the Generalization
  Gate Sprint

---

## Decisions Locked

| Decision | Rationale | Date |
|----------|-----------|------|
| Treat the source telecom dashboard as the parity target | The runtime needs one concrete proof domain before broader generalization | 2026-03-10 |
| Do not claim “any dashboard” support yet | Telco parity is not verified and the proof harness is incomplete | 2026-03-10 |
| Treat `app.py` plus `USE_METADATA` as the main proof path | It shows whether metadata mode can reproduce the real entry point users already know | 2026-03-10 |
| Treat the metadata-only app as secondary | It is useful for isolation, but full proof must also work through the main app path | 2026-03-10 |
| Keep documentation explicit about drift and blockers | The current repo contains mocked proof layers and environment mismatch that must stay visible | 2026-03-10 |

---

## Current Blockers

1. `connie-book/` now has the Symphony reference runtime installed locally and
   connected to Linear, and false `Done` transitions now self-correct, but the
   first clean end-to-end run that writes the expected Connie Book artifact
   (`AI_TOOL_ONBOARDING_GUIDE.md`) back to the live source tree is still not
   complete.
1. Telco pack generation is now deterministic, but it is still normalization of
   the canonical pack rather than true extraction from the legacy dashboard
   surface.

---

## Next Actions Queue

| Rank | Action | Owner | Done When |
|------|--------|-------|-----------|
| 0 | Let `CON-6` complete under the guarded workflow and verify the live artifact | Human or AI | `AI_TOOL_ONBOARDING_GUIDE.md` exists in `connie-book/`, Linear stays aligned, and the post-run guard does not need to reopen the issue |
| 1 | Extend telco pack generation beyond deterministic normalization | Human or AI | The generator derives pack structure from legacy/runtime sources rather than only normalizing the canonical YAML |
| 2 | Decide when to start the Generalization Gate Sprint | Human or AI | The local telco proof gate remains green and the next sprint boundary is documented |

---

## Working Conventions

### Start of session
1. Read `AGENTS.md`
2. Read this file
3. Read `WHERE_AM_I.md`, `result-review.md`, and `sprint-plan.md`
4. Reconfirm whether the work is about metadata boot, telco parity, or future generalization

### End of work unit
1. Update this file if status changed
2. Move completed work into `result-review.md`
3. Adjust `sprint-plan.md`
4. Keep blockers and assumptions explicit

---

## Environment Notes

- Working directory: `/Users/leeharrington/projects/telecom-metadata`
- Primary stack: Python, Streamlit, Pandas, Altair, SQLite, YAML metadata
- Active proof pack: `metadata/dashboard_telco.yaml`
- Source dashboard reference: `/Users/leeharrington/projects/telecomdashboard`

---

This file should describe the real repo state, not the intended marketing story.
