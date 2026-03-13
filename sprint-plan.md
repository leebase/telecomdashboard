# telecom-metadata Sprint Plan

> Tactical plan for the current sprint.

---

## Sprint

**Name**: Telco Parity Proof Sprint  
**Status**: Complete (local proof gate met)  
**Last Updated**: 2026-03-12

---

## Sprint Goal

Repair the metadata runtime enough to boot, then prove that it can reproduce the
source telecom dashboard through metadata with meaningful structural, data, and
visual verification.

### Proposed Next Sprint

**Name**: Generalization Gate Sprint  
**Status**: Proposed

**Goal**: Decide what can safely be abstracted beyond telco only after the
telco proof bar is actually met.

---

## Scope

### In Scope

- Re-baseline AgentFlow docs to the metadata repo
- Restore metadata imports, CLI validation, and runtime boot
- Make the canonical telco pack load in the pinned local environment
- Render the required shell and widget surface in metadata mode
- Implement structural, data, and visual verification against the source dashboard
- Replace mocked or stubbed proof layers with meaningful automation

### Out of Scope For This Sprint

- Claiming broad cross-industry support
- New runtime dependencies unless explicitly approved
- Rewriting the legacy dashboard for aesthetics alone
- Deleting the legacy dashboard path before metadata proof is complete
- Expanding to a second proof domain before telco parity is green

---

## Tasks

| Priority | Task | Status | Notes |
|----------|------|--------|-------|
| P0 | Re-baseline AgentFlow docs | Done | Root-level state and planning docs now exist and describe the metadata repo accurately |
| P0 | Restore metadata runtime imports and validation | Done | Pydantic compatibility repaired and maintained metadata/data/ui tests now run green |
| P0 | Make `metadata/dashboard_telco.yaml` validate and load | Done | `python -m metadata_cli validate metadata/dashboard_telco.yaml` now passes |
| P0 | Prove `USE_METADATA=true streamlit run app.py` boots | Done | Metadata mode starts successfully in headless Streamlit |
| P1 | Fill required shell gaps in metadata mode | Done | Metadata mode now shares the legacy shell and browser-visible parity passes in the local proof baseline |
| P1 | Resolve widget-slot coverage gaps | Done | `metadata.widgets` chart/widget entries resolve through the runtime and the required telco widget surfaces render without placeholders |
| P1 | Add structural parity assertions | Done | `tests/ui/test_app_parity.py` compares tabs, headers, sidebar controls, and time selectors across legacy and metadata paths |
| P1 | Add data parity assertions | Done | `tests/data/test_legacy_metadata_parity.py` compares metadata KPI outputs against the legacy SQLite rollups |
| P2 | Replace mocked visual parity with real browser checks | Done | The harness now uses Playwright-backed real browser screenshots and the six-tab visual proof run passes locally |
| P2 | Replace stub telco-pack generation with deterministic extraction or mapping | Partial | The generator now emits a deterministic normalized snapshot with stable provenance; true extraction or mapping from legacy/runtime sources remains open |
| P2 | Define the telco proof gate explicitly | Done | The sprint now includes a written pass/fail gate tied to validation, maintained tests, visible browser proof, and no placeholders |
| P3 | Register or remove warning-noise in the maintained proof path | Done | `pytest.ini` now loads correctly, registers maintained markers, and the parity path no longer emits the earlier `use_container_width` deprecation noise during manual metadata runs |

## Remediation Workstreams

### Workstream 1: Runtime Boot Repair

**Objective**: Make the metadata runtime load in the pinned local environment.

Tasks:
- Reconcile the Pydantic version split between `requirements.txt` and
  `src/metadata_runtime/models.py`
- Fix any additional loader/model incompatibilities exposed after import is restored
- Re-run the metadata-focused test buckets after the import layer is repaired

Done when:
- `python -m metadata_cli validate metadata/dashboard_telco.yaml` passes
- `pytest tests/metadata tests/data tests/ui -q` runs without import-time failure
- Importing metadata mode through `app.py` no longer crashes immediately

Status:
- Completed on 2026-03-10 for the maintained local proof baseline

### Workstream 2: Telco Pack Execution Repair

**Objective**: Make the canonical pack execute against the local SQLite proof path.

Tasks:
- Fix metadata/schema/runtime mismatches uncovered by real pack validation
- Ensure the pack’s datasource, filters, KPI metrics, and chart bindings all resolve cleanly
- Reconcile any query/view mismatches surfaced by execution tests

Done when:
- The canonical telco pack validates cleanly
- Metadata provider tests and query/view validation tests pass against the local DB
- Metadata mode can render every target subject area without fatal query or binding errors

### Workstream 3: Shell And Widget Parity

**Objective**: Reproduce the target dashboard surface instead of a debug shell.

Tasks:
- Implement metadata-owned rendering for the required shell:
  theme controls, print controls, brand/header framing, and tab rail
- Extend widget resolution beyond KPI cards and charts so required widget slots
  render real output
- Recreate the benchmark-management and KPI-detail surfaces without placeholder fallbacks

Progress update:
- Pack-defined chart/table/form/widget entries from `metadata.widgets` now
  resolve through the runtime and compile against auxiliary metrics correctly
- Metadata mode now reuses the legacy theme, sidebar controls, page header, and
  time-period shell under `AppTest`
- Benchmark management now renders through the metadata pack’s table/history/form
  widgets instead of a runtime bypass
- Browser-visible parity is now green in the local proof baseline

Done when:
- Metadata mode shows the expected shell and section framing
- No required widget slot on the telco proof path resolves to a placeholder
- The first screen looks like the target dashboard rather than a metadata inspector

Status:
- Completed on 2026-03-10 for the current local proof baseline

### Workstream 4: Structural And Data Proof

**Objective**: Make parity claims measurable in automation.

Tasks:
- Add structural assertions for titles, tab order, headers, controls, and section presence
- Add data assertions comparing KPI values, deltas, and chart payloads between legacy and metadata modes
- Add benchmark-surface assertions for required tables and edit surfaces

Done when:
- Structural tests fail on missing tabs, controls, or placeholder sections
- Data tests fail on mismatched KPI values or chart datasets
- The proof path can compare legacy and metadata modes against the same SQLite dataset

Status:
- Completed on 2026-03-10 for the maintained local proof baseline

### Workstream 5: Browser-Level Visual Proof

**Objective**: Replace mocked parity with browser-real evidence.

Tasks:
- Replace fake screenshot capture and diff code with real browser automation
- Capture stable screenshots for all six tabs
- Compare metadata-mode output against the source dashboard reference set with an explicit tolerance

Progress update:
- The harness now uses Playwright-backed real browser screenshots and compares
  against the source screenshot set
- The visual flow rejects blank/background-only captures explicitly
- All six tabs now pass in the local pinned proof environment

Done when:
- Visual parity tests use real screenshots rather than synthetic bytes
- A blank, malformed, or visibly incomplete first screen fails the proof run
- All six tabs participate in the browser proof flow

Status:
- Completed on 2026-03-10 for the current local proof baseline

### Workstream 6: Proof Governance And Pack Generation

**Objective**: Make the parity claim reproducible and hard to overstate.

Tasks:
- Replace or tighten the telco-pack generator so pack evolution is deterministic
- Define the explicit proof gate for “telco parity achieved”
- Document what must pass before the repo can claim broader generality

Done when:
- Pack generation is reproducible enough to diff and review
- The repo has one written proof gate tied to executable checks
- Project docs no longer depend on implied completion

Status:
- Partial on 2026-03-12; the proof gate is written and met locally, and pack
  generation is now deterministic, but true extraction or mapping remains open

### Proposed Next Sprint Tasks

| Priority | Task | Status | Notes |
|----------|------|--------|-------|
| P0 | Decide what abstractions are truly telco-independent | Proposed | Use telco proof findings rather than assumptions |
| P0 | Define a second proof pack candidate | Proposed | Only after telco parity passes |
| P1 | Harden metadata authoring ergonomics | Proposed | Better generation, validation, and debugging workflows |
| P1 | Re-evaluate packaging and dependency boundaries | Proposed | Depends on proof-path stability |

---

## Definition of Done

- Metadata runtime imports successfully in the supported local environment
- The canonical telco pack validates and loads
- Metadata mode reproduces the required shell, subject-area tabs, and key widget surfaces
- Structural, data, and browser parity checks all run with meaningful pass/fail behavior
- The repo can make a narrow, defensible claim: telco dashboard reproduction via metadata is proven

## Telco Proof Gate

The repo may only claim `telco parity achieved` when all of the following are
true in the current local proof environment:

1. `python -m metadata_cli validate metadata/dashboard_telco.yaml` passes.
2. `pytest tests/metadata tests/data tests/ui -q` passes.
3. `pytest tests/visual/test_visual_parity.py -q -m visual` passes with
   browser-visible screenshots for all six tabs.
4. `USE_METADATA=true streamlit run app.py` renders a visibly populated first
   screen in a browser, including the intended tabs and primary KPI region.
5. No required telco subject area relies on placeholder output for its required
   shell, KPI, chart, or benchmark-management surface.

Current status:
- Met on 2026-03-10 in the pinned local proof environment.
- Caveat: pack generation hardening remains open.

### Verification Commands

1. `python -m metadata_cli validate metadata/dashboard_telco.yaml`
2. `pytest tests/metadata tests/data tests/ui -q`
3. `USE_METADATA=true streamlit run app.py`
4. Browser render check of the first screen and all six tabs
5. Parity test suite covering structural, data, and visual checks

---

## Risks

| Risk | Mitigation |
|------|------------|
| Dependency drift keeps the runtime from booting | Fix environment/runtime mismatch before deeper parity work |
| Placeholder proof code creates false confidence | Replace mocked screenshot and parity behavior with browser-real checks |
| Legacy coupling hides missing abstractions | Keep architecture docs explicit and verify runtime-owned behavior |
| Scope expansion dilutes proof work | Hold the sprint boundary at telco parity only |

---

## Notes

The first objective is proof-path honesty. The second objective is proof-path completion.

Parallel workspace note:
- `connie-book/` now exists as a separate repo-local planning workspace for a
  Symphony-oriented book-writing and AI-learning project.
- It is intentionally outside the telco parity claim and should not be used as
  evidence of metadata-runtime generalization.
- It now has an hourly runbook, a self-improving workflow contract, and a live
  Linear-backed Symphony runtime.
- The remaining Connie Book follow-up is now narrower: the tracker-backed
  runtime has a tested post-run guard against false `Done` transitions, and the
  next proof point is one clean artifact-producing run that writes the finished
  file back into the live source tree without needing that guard.
- The telco pack generator has moved from a dated stub to deterministic
  normalization, so the next generator step is deriving pack content from
  legacy/runtime inputs instead of only rewriting canonical YAML.

### Execution Plan

1. Fix the metadata boot and validation path.
2. Close the shell and widget gaps in metadata mode.
3. Build structural and data parity checks.
4. Add browser-level visual proof.
5. Update session docs with concrete results rather than intent.

### Current Sequencing

1. Decide what legacy coupling remains acceptable in metadata mode
2. Harden pack generation now that the proof gate is green
3. Start the Generalization Gate Sprint only after those follow-ups are scoped
