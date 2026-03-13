# telecom-metadata Result Review

> Running log of completed work. Newest entries first.

## 2026-03-12 — Telco Pack Generator Hardened To Deterministic Normalization

### What changed

- Reworked `tools/generate_telco_metadata.py` so generation is now a
  deterministic normalization step with stable provenance metadata instead of a
  dated Sprint 4 stub
- Added focused coverage in `tests/unit/test_generate_telco_metadata.py`
- Regenerated `metadata/dashboard_telco_generated.yaml` from the current
  canonical pack

### What was verified

1. `source .venv/bin/activate && pytest tests/unit/test_generate_telco_metadata.py -q` passes
2. `source .venv/bin/activate && python tools/generate_telco_metadata.py --output metadata/dashboard_telco_generated.yaml --validate` passes

### Why it matters

Pack generation is now reproducible enough to diff and review, which lowers the
risk of silent drift in the proof pack. The remaining gap is no longer
determinism; it is moving from normalization into genuine extraction or mapping
from legacy/runtime sources.

### Remaining follow-up

- Decide which legacy/runtime surfaces should become the first true generator
  inputs
- Extend the generator beyond canonical-pack normalization
- Keep the generated pack aligned with the canonical telco pack as those inputs
  harden

## 2026-03-10 — Connie Book Post-Run Completion Guard Implemented And Validated

### What changed

- Added `connie-book/scripts/enforce-after-run.sh` as a repo-owned Symphony
  `after_run` guard
- Updated `connie-book/WORKFLOW.md` so the guard now owns both subtree writeback
  and artifact-gated tracker enforcement
- Updated `connie-book/SYMPHONY_SETUP.md`, `connie-book/BACKLOG.md`, and
  `connie-book/RUN_LOG.md` to reflect the new runtime contract and validation

### What was verified

1. Forcing `CON-6` back to Linear `Done` now triggers the guard to reopen it to
   `Todo` when `connie-book/AI_TOOL_ONBOARDING_GUIDE.md` is still missing
2. The guard appends a new Linear comment explaining why the issue was
   reopened
3. Restarting Symphony through `zsh -lic` restores `LINEAR_API_KEY` visibility,
   and the daemon claims `CON-6` again under the corrected workflow

### Why it matters

The Connie Book runtime no longer depends on prompt compliance alone for
artifact-gated completion. The remaining task is now the substantive one:
getting a clean agent run that produces the onboarding-guide artifact.

### Remaining follow-up

- Let the live `CON-6` run finish under the guarded workflow
- Confirm `connie-book/AI_TOOL_ONBOARDING_GUIDE.md` appears in the live tree
- Verify the issue reaches `Done` without the guard needing to intervene

## 2026-03-10 — Benchmark Management Now Renders Through Metadata

### What changed

- Removed the legacy `create_benchmark_tab()` shortcut from
  `src/ui/metadata_runtime_app.py`
- Let the benchmark-management tab flow through the metadata layout and widget
  registry using the pack-defined benchmark table, history table, and editor
  widgets
- Added a benchmark-specific metadata app parity assertion in
  `tests/ui/test_app_parity.py`

### What was verified

1. `source .venv/bin/activate && pytest tests/metadata tests/data tests/ui -q` passes with 86 passing tests and 2 skips
2. `source .venv/bin/activate && pytest tests/visual/test_visual_parity.py -q -m visual` passes with all 6 tabs green
3. `source .venv/bin/activate && python -m metadata_cli validate metadata/dashboard_telco.yaml` passes

### Why it matters

The local telco proof path no longer depends on the legacy benchmark manager
for its sixth tab. The benchmark-management surface is now part of the
metadata-owned runtime rather than a runtime bypass.

### Remaining follow-up

- Harden or replace the telco pack generator
- Decide when the local telco proof is strong enough to start the
  Generalization Gate Sprint

---

## 2026-03-10 — Connie Book Backlog Captured A Replace-Linear Follow-Up

## 2026-03-10 — Connie Book Symphony Workspace Bootstrap Repaired

## 2026-03-10 — Connie Book Workflow Hardened After A False `Done`

### What changed

- Reopened `CON-6` after the live Symphony run moved it to `Done` without
  leaving `AI_TOOL_ONBOARDING_GUIDE.md` in the live `connie-book/` tree
- Updated `connie-book/WORKFLOW.md` so a run cannot move an item to `Done`
  without a concrete live-tree artifact check after sync
- Updated `connie-book/BACKLOG.md` so `CBOOK-008` now names its required file
  explicitly: `connie-book/AI_TOOL_ONBOARDING_GUIDE.md`
- Logged the failure and correction in `connie-book/RUN_LOG.md` and
  `connie-book/SYMPHONY_SETUP.md`

### What was verified

1. Linear had `CON-6` in `Done`
2. The live `connie-book/` source tree still had no onboarding-guide artifact
3. Reopening `CON-6` to `Todo` succeeded
4. The new workflow now blocks closure when artifact evidence is missing or
   ambiguous

### Why it matters

The remaining Connie Book risk is no longer basic runtime wiring. It is
evidence discipline. The workflow now has a stronger contract against false
completion, which is the right next layer of hardening for a tracker-backed
agent loop.

### Remaining follow-up

- Let Symphony retry `CON-6` under the stricter completion rules
- Confirm the onboarding guide lands at the named live artifact path
- Verify repeated tracker-backed runs stay aligned with live-tree evidence

---

### What changed

- Repaired the moved `telecom-metadata` git worktree with
  `git worktree repair /Users/leeharrington/projects/telecom-metadata`
- Updated `connie-book/WORKFLOW.md` to replace the rejected workspace-symlink
  approach with:
  - a real repo clone inside each issue workspace
  - a live working-tree overlay before each run
  - an `after_run` sync of `connie-book/` back to the live repo
- Updated `connie-book/SYMPHONY_SETUP.md` and `connie-book/RUN_LOG.md` to
  document the bootstrap failure and the repaired design

### What was verified

1. The old workspace-symlink approach fails under upstream Symphony with
   `:symlink_escape` and `:workspace_outside_root`
2. After removing the stale symlinked issue workspace, Symphony creates a real
   repo-backed `CON-6` workspace under
   `~/code/symphony-workspaces/connie-book/CON-6`
3. The repaired runtime reaches a live Codex session for `CON-6` instead of
   failing during workspace validation

### Why it matters

The tracker-backed Connie Book runtime is now operating inside an upstream-
compatible workspace model instead of a brittle local shortcut. The remaining
gap is no longer bootstrap safety; it is completion of the first end-to-end
artifact-producing run.

### Remaining follow-up

- Let the active `CON-6` run finish or tune it if it stalls
- Confirm the onboarding-guide artifact syncs back into the live
  `connie-book/` source tree
- Verify the matching Linear issue state reflects the actual artifact evidence

---

### What changed

- Added `CBOOK-014 Replace Linear with a project-owned tracker adapter` to
  `connie-book/BACKLOG.md`
- Logged the decision in `connie-book/RUN_LOG.md`

### Why it matters

The project now explicitly records the strategy preference to benefit from
upstream Symphony while avoiding long-term lock-in to Linear.

### Remaining follow-up

- Stand up the first real tracker-backed Symphony loop
- Use that real integration experience to define the smallest replacement
  tracker interface

---

## 2026-03-10 — Connie Book Linear Project Wired Into The Workflow

### What changed

- Updated `connie-book/WORKFLOW.md` to use the real Linear `project_slug`
  `connie-book-5960e2522285` from the provided project URL
- Recorded the tracker target in `connie-book/SYMPHONY_SETUP.md`

### Why it matters

The workflow is now pointed at the actual Connie Book Linear project instead of
using a placeholder value. The remaining runtime blocker is the Linear API key.

### Remaining follow-up

- Set `LINEAR_API_KEY` in the local shell environment
- Start Symphony against the Connie Book workflow

---

## 2026-03-10 — Connie Book Symphony Runtime Advanced To Real Agent Runs

### What changed

- Upgraded local `codex` from `0.46.0` to `0.113.0`
- Updated `connie-book/WORKFLOW.md` to use:
  - the full Linear project slug
  - the upstream-style Codex app-server command
  - an increased `codex.read_timeout_ms`
- Created the first real Linear issues for Connie Book work:
  - `CON-5` for hourly automation
  - `CON-6` for the AI tool onboarding guide
  - `CON-7` for workflow improvement

### What was verified

1. Symphony starts against the real Connie Book Linear project
2. Symphony claims Linear issues from the project
3. After the Codex upgrade, the service reaches live Codex session and turn
   events instead of failing immediately on protocol mismatch
4. A live Symphony daemon is now running against the Connie Book workflow and
   polling the Linear project continuously

### Why it matters

The project is now running on the real upstream Symphony stack rather than only
on local planning files. Remaining issues are runtime-tuning details, not basic
installation or tracker wiring.

### Remaining follow-up

- Keep Symphony running with the updated workflow settings
- Confirm the first issue completes and writes back the expected artifacts
- Tune timeouts or prompt behavior if `CON-5` continues to retry

---

## 2026-03-10 — Connie Book Symphony Bootstrap Workspace Created

### What changed

- Created a new repo-local planning workspace in `connie-book/` for a
  daughter-first book-writing and AI-learning program
- Added the first source-of-truth artifacts:
  - `connie-book/PROJECT_BRIEF.md`
  - `connie-book/ROADMAP.md`
  - `connie-book/LESSON_PLAN.md`
  - `connie-book/BACKLOG.md`
  - `connie-book/WORKFLOW.md`
  - `connie-book/RUN_LOG.md`
  - `connie-book/agents/*.md`
- Seeded the workspace with a 12-week curriculum, issue-like backlog entries,
  Symphony-compatible workflow instructions, and two initial run-log entries
- Added `connie-book/HOURLY_ORCHESTRATION.md` and `connie-book/SYMPHONY_SETUP.md`
  so the operating path is now explicit: live hourly automation first, full
  tracker-backed Symphony later
- Updated `connie-book/WORKFLOW.md` to require a workflow-and-agent improvement
  pass at the end of every run
- Promoted hourly automation activation into the active backlog and added a
  dedicated backlog item for improving agent missions and workflow feedback
- Kept the new workspace explicitly separate from the telco proof claim so the
  repo does not accidentally imply product-scope expansion

### What was verified

1. The required `connie-book/` planning files and agent mission files now exist
2. The lesson plan covers all 12 weeks and includes writing goal, AI goal,
   deliverable, exercise, time budget, and artifact for each week
3. The backlog items include owner agents, dependencies, states, and
   definitions of done
4. The workflow contract includes YAML front matter and a prompt body aligned
   with the current Symphony repo model
5. `RUN_LOG.md` contains explicit sample runs from item selection through proof
   of work
6. The hourly runbook and setup notes now describe how to operate the project as
   a live orchestrated loop instead of a static documentation set

### Why it matters

The repo now has a concrete, usable workspace for learning Symphony-style
orchestration through a real family-centered project instead of a detached demo.
It also gives the project a low-friction operating system that can later be
connected to real automation.

### Remaining follow-up

- Activate the real hourly automation loop for `connie-book/`
- Decide the book category and reader promise as the first substantive content
  item
- Build the Week 1 packet and AI tool onboarding guide

---

## 2026-03-10 — Symphony Reference Runtime Installed Locally

### What changed

- Cloned `openai/symphony` into `connie-book/symphony-reference`
- Installed the missing local runtime requirements with Homebrew:
  - `mise`
  - `erlang`
  - `elixir`
- Built the Elixir reference implementation in
  `connie-book/symphony-reference/elixir`

### What was verified

1. `mise --version` succeeds locally
2. `elixir --version` succeeds locally
3. `connie-book/symphony-reference/elixir/bin/symphony --help` prints the CLI
   usage successfully

### Why it matters

The project is no longer limited to a Symphony-shaped local workflow. The real
reference implementation is now installed and buildable on this machine. The
remaining blocker is tracker credential and project wiring, not local runtime
availability.

### Remaining follow-up

- Create a Linear personal API key and set `LINEAR_API_KEY`
- Create or confirm the target Linear project for Connie Book work
- Replace placeholder tracker values in `connie-book/WORKFLOW.md`
- Start the real Symphony service against the intended workflow

---

## 2026-03-10 — `use_container_width` Warning Cleanup Completed For The Parity Path

### What changed

- Replaced deprecated `use_container_width` button/dataframe/data-editor calls
  in the active metadata parity path and nearby dashboard surfaces where the
  pinned Streamlit version supports `width=...`
- Kept `st.altair_chart(..., use_container_width=True)` in place because this
  pinned Streamlit version does not yet accept `width=` for Altair charts

### What was verified

1. `source .venv/bin/activate && pytest tests/metadata tests/data tests/ui -q` passes with 85 passing tests and 2 skips
2. `source .venv/bin/activate && pytest tests/visual/test_visual_parity.py -q -m visual` passes with all 6 tabs green
3. `source .venv/bin/activate && USE_METADATA=true .venv/bin/streamlit run app.py --server.headless true --server.port 64722` followed by a real browser page load no longer emits the prior `use_container_width` deprecation warnings

### Why it matters

The local proof path is cleaner and less fragile. The app now runs without the
manual metadata-mode warning noise that was still leaking through after the
proof gate first went green.

### Remaining follow-up

- Decide whether the current benchmark-tab legacy coupling is an acceptable
  interim parity shortcut or should be modeled directly in metadata
- Harden or replace the telco pack generator

---

## 2026-03-10 — Browser-Visible Blank Screen Fixed And Visual Proof Went Green

### What changed

- Switched the browser capture path in `src/ui/visual_parity.py` to prefer
  Playwright screenshots with a button-count readiness check instead of the
  brittle hidden-container wait
- Added a unit test proving `capture_screenshot()` routes into the browser
  backend when `app_url` is configured
- Fixed the active theme styles in
  `styles/cognizant/cognizant.css` and `styles/verizon/verizon.css` by removing
  CSS that hid `.stApp > div:first-child` in current Streamlit builds

### What was verified

1. `source .venv/bin/activate && pytest tests/ui/test_visual_parity.py -q` passes with 23 passing tests
2. `source .venv/bin/activate && pytest tests/metadata tests/data tests/ui -q` passes with 85 passing tests and 2 skips
3. `source .venv/bin/activate && python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
4. `source .venv/bin/activate && pytest tests/visual/test_visual_parity.py -q -m visual` passes with all 6 tabs green
5. Manual browser inspection confirmed that the first metadata screen is visibly populated again once the broken theme CSS is removed

### Why it matters

The local telco proof gate is now actually satisfied. The browser surface is no
longer blank, the visual harness is using real screenshots, and the six-tab
proof run is green in the pinned local environment.

### Remaining follow-up

- Decide whether the current benchmark-tab legacy coupling is an acceptable
  interim parity shortcut or should be modeled directly in metadata
- Clean up `use_container_width` deprecation warnings in manual Streamlit runs
- Harden or replace the telco pack generator

---

## 2026-03-10 — Playwright Installed In Local Proof Environment

### What changed

- Installed `playwright` into the local repo virtualenv
- Installed the Playwright-managed Chromium browser locally

### What was verified

1. `source .venv/bin/activate && python - <<'PY' ... sync_playwright() ... PY` launches Chromium headlessly and reads a test page successfully

### Why it matters

The next browser-proof pass can move to Playwright-backed screenshot capture
without more local environment setup.

### Remaining follow-up

- Keep the Playwright-backed visual harness aligned with the local browser-proof path

---

## 2026-03-10 — Browser Proof Hardened To Reject Background-Only Captures

### What changed

- Added low-variance screenshot rejection in `src/ui/visual_parity.py` so the
  browser proof fails immediately when Chrome returns only the dark shell
  background instead of visible UI
- Added unit coverage in `tests/ui/test_visual_parity.py` for the new
  background-only capture guard
- Wrote the explicit telco proof gate into `sprint-plan.md`

### What was verified

1. `source .venv/bin/activate && pytest tests/ui/test_visual_parity.py -q` passes with 22 passing tests
2. `source .venv/bin/activate && pytest tests/metadata tests/data tests/ui -q` passes with 84 passing tests and 2 skips
3. `source .venv/bin/activate && python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
4. `source .venv/bin/activate && pytest tests/visual/test_visual_parity.py -q -m visual` now fails all 6 tabs with the explicit message `Captured screenshot appears background-only`

### Why it matters

The visual proof path is now more honest. It no longer reports misleading
partial success when the browser capture backend is only returning the theme
background instead of a visible dashboard render.

### Remaining follow-up

- Repair or replace the local browser capture backend so screenshots contain
  real visible UI
- Re-run the six-tab browser proof once the backend is trustworthy
- Decide whether the current benchmark-tab legacy coupling is an acceptable
  interim parity shortcut or should be modeled directly in metadata

---

## 2026-03-10 — Structural/Data Proof Landed And Browser Visual Proof Became Real

### What changed

- Reused the legacy shell primitives in metadata mode so both app paths now
  expose matching sidebar controls, page headers, and tab rails
- Fixed stale SQLite query drift in `database_connection.py` so the legacy app
  renders cleanly again against the rebuilt proof database
- Added structural parity coverage in `tests/ui/test_app_parity.py`
- Added legacy-vs-metadata network KPI parity coverage in
  `tests/data/test_legacy_metadata_parity.py`
- Replaced the synthetic visual harness in `src/ui/visual_parity.py` with a
  real headless-Chrome screenshot capture path and PIL-based diffing
- Reworked `tests/visual/test_visual_parity.py` into an opt-in browser-real
  parity suite against the source screenshot set
- Fixed cache persistence serialization and cleanup drift in `src/data/cache.py`
- Corrected `pytest.ini` so pytest loads the repo config, registers the
  `integration` and `visual` markers, and no longer requires the absent
  `pytest-cov` plugin for local proof runs

### What was verified

1. `source .venv/bin/activate && pytest tests/metadata tests/data tests/ui -q` passes with 82 passing tests and 2 skips
2. `source .venv/bin/activate && python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
3. `source .venv/bin/activate && pytest tests/visual/test_visual_parity.py -q -m visual` runs browser-real screenshot diffs against the source reference set
4. The initial browser proof run showed the harness reaching real screenshots,
   but later hardening exposed that the local capture backend is still not
   trustworthy enough to certify visible parity

### Why it matters

The proof story is no longer mostly aspirational. Structural/data parity is now
executable and green in the maintained suite, and visual parity is measured by
real browser screenshots rather than synthetic bytes.

### Remaining follow-up

- Repair the browser screenshot backend so visible parity can actually be
  measured
- Decide whether the current benchmark-tab legacy coupling is an acceptable
  interim step or should be modeled directly in metadata
- Keep the explicit telco proof gate aligned with the real browser-proof state

---

## 2026-03-10 — Metadata Widget And Chart Override Resolution Expanded

### What changed

- Extended `src/ui/metadata_runtime_app.py` so layout slots can resolve entries
  from `metadata.widgets`, not just KPI primary/secondary definitions
- Added dataset-backed payload assembly for pack-defined widget overrides in
  `src/data/metadata_provider.py`
- Extended `src/ui/metadata_widgets.py` with the remaining chart renderers used
  by the canonical telco pack: `stacked_bar`, `multi_series_line`,
  `forecast_band`, and `heatmap`
- Fixed `src/data/query_compiler.py` so auxiliary metrics compile correctly
  when pack-defined widgets reference them
- Tightened metadata validation so widget override datasets must point to a
  defined KPI or auxiliary metric
- Added focused tests for resolver behavior, widget payloads, registry coverage,
  and auxiliary-metric compilation

### What was verified

1. `source .venv/bin/activate && pytest tests/data/test_metadata_provider.py tests/data/test_query_compiler.py tests/ui/test_widget_registry.py tests/ui/test_metadata_runtime_app.py -q` passes with 12 passing tests
2. `source .venv/bin/activate && pytest tests/metadata tests/data tests/ui -q` passes with 78 passing tests, 2 skips, and the previously known `integration` marker warnings
3. `source .venv/bin/activate && python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
4. `source .venv/bin/activate && USE_METADATA=true streamlit run app.py --server.headless true --server.port 8516` starts successfully

### Why it matters

This closes a concrete execution gap in the telco proof path. The canonical
pack can now route its standalone chart/table/form/widget entries through the
runtime instead of dropping them immediately to placeholder output.

### Remaining follow-up

- Confirm the first populated metadata screen is browser-visibly acceptable, not
  just non-crashing
- Close the branded shell gap in metadata mode
- Replace mocked visual parity with browser-real evidence

---

## 2026-03-10 — AgentFlow Docs Re-Baselined

### What changed

- Replaced the generic root `AGENTS.md` with an AgentFlow-style project guide
- Added the missing session-state files:
  - `context.md`
  - `WHERE_AM_I.md`
  - `result-review.md`
  - `sprint-plan.md`
  - `product-definition.md`
  - `project-definition.md`
  - `architecture.md`
- Added metadata-specific planning docs:
  - `project-description.md`
  - `design.md`
  - `project-plan.md`

### Why it matters

The repo now has a working documentation baseline that reflects what
`telecom-metadata` actually is: a metadata-runtime proof repo with meaningful
implementation progress, visible drift, and unfinished parity verification.

### How to verify

1. Open `AGENTS.md`
2. Confirm the startup protocol points to the new root-level state files
3. Confirm the new docs describe `telecom-metadata`, not `telecomdashboard`
4. Confirm the docs do not claim telco parity is already proven

---

## 2026-03-10 — Remediation Sprint Plan Expanded

### What changed

- Reworked `sprint-plan.md` from a short parity outline into a detailed
  remediation plan
- Added six explicit workstreams:
  - runtime boot repair
  - telco pack execution repair
  - shell and widget parity
  - structural and data proof
  - browser-level visual proof
  - proof governance and pack generation
- Added concrete verification commands and sequencing so future work can be
  executed in the correct order

### Why it matters

The repo now has a more implementation-ready sprint plan for fixing the exact
issues already identified in the docs and code review, rather than only naming
the problem areas at a high level.

### How to verify

1. Open `sprint-plan.md`
2. Confirm the remediation workstreams are explicit and ordered
3. Confirm the plan covers every known blocker: boot, pack execution, shell,
   widget coverage, structural/data proof, and browser proof

---

## 2026-03-10 — Metadata Boot And Validation Restored

### What changed

- Converted `src/metadata_runtime/models.py` from Pydantic v2-only validator
  usage to Pydantic v1-compatible validation
- Relaxed datasource-model validation so Snowflake DSN enforcement happens in
  the runtime layer where the tests expect it
- Fixed SQLite datasource error propagation so failed metadata queries raise
  `DataSourceError` cleanly and can fall back when appropriate
- Repaired stale SQLite view definitions in `scripts/create_views.py`
- Rebuilt views in `data/telecom_db.sqlite` so the checked-in proof database
  matches the corrected definitions
- Fixed `src/ui/visual_parity.py` bugs in DOM comparison and baseline
  save/load behavior
- Added a local `snowflake` stub package so Snowflake unit tests can patch
  `snowflake.connector.connect` without the optional dependency installed

### What was verified

1. `source .venv/bin/activate && python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
2. `source .venv/bin/activate && python -m pytest tests/metadata tests/data tests/ui -q` passes with 72 passing tests and 2 skips
3. `source .venv/bin/activate && USE_METADATA=true streamlit run app.py --server.headless true --server.port 8515` starts successfully
4. A bare Python import of `app.py` with `USE_METADATA=true` now completes without the prior Pydantic import crash

### Why it matters

This restores the local metadata proof baseline. The repo is no longer blocked
at import time, and the maintained metadata/data/ui test surface is green
enough to move on to shell parity and real proof automation.

### Remaining follow-up

- Register or clean up the remaining `integration` marker warnings
- Investigate the cache persistence warnings seen during bare-script imports
- Replace mocked visual parity with browser-real evidence
- Close the shell and widget parity gaps

---

## Pre-2026-03-10 — Metadata Runtime Foundation Present At Intake

### What existed

- Metadata runtime modules under `src/metadata_runtime/`
- UI/runtime code under `src/ui/`
- Datasource, cache, provider, and query-compiler code under `src/data/`
- A metadata-only app entry point at `apps/meta/app.py`
- A feature-flag path in `app.py` that routes to metadata mode via `USE_METADATA`
- A canonical telco pack at `metadata/dashboard_telco.yaml`

### Why it matters

The repo is past the idea stage. It already contains a meaningful slice of the
runtime and a concrete proof domain. The remaining issue is not lack of code;
it is proof, completeness, and drift control.

---

## Pre-2026-03-10 — Query And View Validation Layers Added

### What existed

- Metadata query integration tests in `tests/data/test_metadata_query_integration.py`
- View/schema validation tests in `tests/data/test_view_validation.py`
- Metadata provider tests in `tests/data/test_metadata_provider.py`
- Metadata model, loader, dialect, and UI/layout test files under `tests/metadata/`
  and `tests/ui/`

### Why it matters

The repo already has useful proof scaffolding for query correctness and
metadata-data wiring. That work should be preserved and extended rather than
replaced.

### Current gap

These layers do not yet amount to a full parity claim. Runtime boot,
widget completeness, and browser-visible verification still need to be made real.

---

## Pre-2026-03-10 — Parity Proof Intent Exists But Is Incomplete

### What existed

- `src/ui/visual_parity.py` for parity-oriented tooling
- `tests/visual/test_visual_parity.py` for screenshot and parity tests
- `tools/generate_telco_metadata.py` for telco-pack generation support
- Refactor docs that describe the parity objective

### Why it matters

The desired proof direction is already explicit in the repo.

### Current gap

- Visual parity code is mocked, not browser-real
- Screenshot comparisons are placeholders
- The telco generator is not true legacy introspection
- The current proof story is not strong enough to claim the dashboard has been reproduced
