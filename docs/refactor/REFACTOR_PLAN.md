# Refactor Plan – Metadata Runtime Migration

## Approach
Deliver the metadata runtime behind a feature flag (`USE_METADATA`) to guarantee parity with the incumbent hard-coded dashboard. Work proceeds in parallel epics covering schema, UI rendering, data adapters, migration, and documentation. Each story concludes with validation commands and rollback steps.

## Zero-Downtime Strategy
- Implement feature flag scaffolding in `app.py` and `runAgentsApp.py` (default `False`).
- Build metadata runtime against the flag, keeping legacy code path unchanged.
- Run visual regression + golden CSV tests before flipping flag in staging.
- Launch via progressive rollout (internal → pilot → production); retain switch for hot rollback.

---

## Epic A – Metadata Schema & Loader

### A1. Author Pydantic Models & JSON Schema
- [x] **Status:** Completed (Pydantic models + validation tests in `src/metadata_runtime/models.py`)
- **Files:** `src/metadata_runtime/models.py`, `src/metadata_runtime/__init__.py`.
- **Acceptance:** Models cover all schema fields (globals, dialects, data_sources, filters, subject_areas, kpis, security, refresh). Validation errors emit actionable messages.
- **Diffs:** New module; unit tests in `tests/metadata/test_models.py`.
- **Tests:** `pytest tests/metadata/test_models.py`.
- **Risk/Rollback:** Low—new files only; delete module if blocking.
- **Effort:** 3 points.

### A2. YAML Loader & Validator CLI
- [x] **Status:** Completed (loader + CLI shipped with caching and unit tests)
- **Files:** `src/metadata_runtime/loader.py`, `metadata_cli.py`, `pyproject` entry point.
- **Acceptance:** CLI `metadata_cli validate <file>` parses YAML, applies models, prints summary + line references.
- **Diffs:** Loader, CLI, wiring in `setup.cfg`/`pyproject.toml`.
- **Tests:** `pytest tests/metadata/test_loader.py` with fixture YAMLs.
- **Risk/Rollback:** Medium—CLI wiring may break packaging. Rollback by disabling console entry point.
- **Effort:** 3 points.

### A3. Dialect Macro System Design & Stubs
- [x] **Status:** Completed (Sprint 3 macro registry + template modules)
- **Files:** `src/metadata_runtime/dialects/__init__.py`, `metadata/macros/*.sql`, `tests/metadata/test_dialects.py`.
- **Acceptance:** Macro registry loads per dialect; rendering stub returns compiled SQL string; tests assert macro substitution for date trunc, QUALIFY emulation, limit syntax.
- **Diffs:** New macro registry + Jinja macro templates co-located with packs; regression tests cover snowflake/sqlite rendering.
- **Tests:** `pytest tests/metadata/test_dialects.py`.
- **Risk/Rollback:** Low; remove registry and templates if blocking compilation.
- **Effort:** 2 points.

---

## Epic B – Widget Registry & Layout Interpreter

### B0. Meta App Bootstrap (Streamlit Shell)
- [x] **Status:** Completed (Sprint 1 metadata-driven tab scaffold)
- **Files:** `apps/meta/app.py`, `tests/metadata/test_loader.py` (smoke asserts), logging utilities.
- **Acceptance:** Meta app reads metadata once, renders tab navigation from subject areas, and logs single-load behaviour.
- **Diffs:** New meta app entrypoint with feature flag guard; wiring documented in `docs/refactor/CONFIGURE.md`.
- **Tests:** Manual `streamlit run apps/meta/app.py`; lazy smoke in metadata tests.
- **Risk/Rollback:** Low—isolated demo app.
- **Effort:** 2 points.

### B1. Widget Registry Mapping
- [x] **Status:** Completed (Sprint 2 MVP for cards + line/bar/area charts)
- **Files:** `src/ui/metadata_widgets.py`, `tests/ui/test_widget_registry.py`.
- **Acceptance:** Registry maps metadata `type` values (`kpi_card`, `timeseries_line`, `bar_chart`, `area_chart`) to callable factories; fallbacks log warnings.
- **Diffs:** New registry module registered default widgets; tests exercise registration overrides.
- **Tests:** `pytest tests/ui/test_widget_registry.py` using fake metadata payloads.
- **Risk/Rollback:** Medium—touches shared UI helpers. Rollback by reverting registry imports and stubs.
- **Effort:** 4 points.

### B2. Layout Interpreter (12-Column Grid)
- [x] **Status:** Completed (Sprint 2 limited to Network Performance tab)
- **Files:** `src/ui/layout_engine.py`, `apps/meta/app.py`, `tests/ui/test_layout_engine.py`.
- **Acceptance:** Layout interpreter renders metadata rows/columns and delegates to widget registry for cards/charts.
- **Diffs:** New engine + meta app integration (network tab only).
- **Tests:** `pytest tests/ui/test_layout_engine.py`.
- **Risk/Rollback:** High—touches `app.py`. Rollback by toggling flag to false and reverting hook.
- **Effort:** 5 points.

---

## Epic C – Data Layer & Caching

### C1. DataSource Abstraction & Connection Factory
- [x] **Status:** Completed (Sprint 3 datasource factory + SQLite/Snowflake adapters)
- **Files:** `src/data/datasource.py`, `tests/data/test_datasource.py`.
- **Acceptance:** Factory supports Snowflake (env-keyed DSN) and SQLite; includes health check logging and fallback handling.
- **Diffs:** New abstraction with datasource error propagation; legacy `database_connection.py` remains for non-metadata mode.
- **Tests:** `pytest tests/data/test_datasource.py`.
- **Risk/Rollback:** Medium—Snowflake connector dependency required in metadata mode. Rollback by forcing factory to return stub datasource.
- **Effort:** 5 points.
- **Note:** Sprint 2 stub provider replaced by runtime-backed provider with deterministic fallback when datasources unavailable.

### C2. Query Compilation & Filter Binding
- [x] **Status:** Completed (Sprint 3 Jinja compiler + filter bindings)
- **Files:** `src/data/query_compiler.py`, `tests/data/test_query_compiler.py`.
- **Acceptance:** Compiler merges default filters, renders SQL via macros, exposes compiled query metadata for datasource execution.
- **Diffs:** New compiler module with quoting/csv filters and date-range resolver.
- **Tests:** `pytest tests/data/test_query_compiler.py`.
- **Risk/Rollback:** Medium; bypass compiler by returning stub SQL when metadata flag disabled.
- **Effort:** 4 points.

### C3. Caching Policy & Invalidation
- [ ] **Status:** Not started
- **Files:** `src/data/cache.py`, integrate with existing `cache_with_ttl` decorator.
- **Acceptance:** Cache respects metadata TTL, keyed by KPI + filters, supports SQLite materialized cache optional.
- **Diffs:** New cache module + optional CLI `metadata_cli cache clear` command.
- **Tests:** `pytest tests/data/test_cache.py`.
- **Risk/Rollback:** Low—flagged usage. Rollback by disabling metadata cache call.
- **Effort:** 3 points.

---

## Epic D – Migration & Compatibility

### D1. Inventory & Auto-Generate Telco Metadata
- [ ] **Status:** Not started
- **Files:** `tools/generate_telco_metadata.py`, `metadata/dashboard_telco.yaml` (output of this pass).
- **Acceptance:** Script introspects legacy code (metrics, charts, filters) and emits metadata identical to hand-authored pack; diff is tracked and reviewed.
- **Diffs:** New tooling; YAML lives in repo.
- **Tests:** `pytest tests/tools/test_generate_telco_metadata.py` comparing sample output to fixture.
- **Risk/Rollback:** Low—tooling only. Rollback by removing script.
- **Effort:** 3 points.

### D2. Feature Flag Integration & Runtime Switch
- [x] **Status:** Completed (Sprint 3 runtime switch + helper module)
- **Files:** `app.py`, `runAgentsApp.py`, `src/ui/runtime_switch.py`, `src/ui/metadata_runtime_app.py`, `tests/ui/test_runtime_switch.py`.
- **Acceptance:** `USE_METADATA` flag routes primary apps to metadata runtime; legacy path untouched when flag false; logging documents active mode.
- **Diffs:** Early flag guard in entrypoints, reusable metadata renderer shared with `apps/meta/app.py`.
- **Tests:** `pytest tests/ui/test_runtime_switch.py` plus manual smoke via Streamlit.
- **Risk/Rollback:** High—affects entrypoint. Rollback by unsetting flag or removing guard.
- **Effort:** 4 points.

### D3. Visual Parity Verification
- [ ] **Status:** Not started
- **Files:** `tests/visual/test_visual_parity.py`, baseline assets under `tests/visual/baseline/`.
- **Acceptance:** Headless renderer captures screenshots/DOM snapshots per subject area; comparison tolerance ≤2%.
- **Diffs:** Visual test harness, baseline assets.
- **Tests:** `pytest tests/visual/test_visual_parity.py -m visual`.
- **Risk/Rollback:** Medium—visual tests brittle. Rollback by quarantining marker.
- **Effort:** 3 points.

---

## Epic E – Documentation & Examples

### E1. Operator & Extender Docs
- [x] **Status:** Completed (initial architecture/config docs authored in design pass)
- **Files:** `docs/CONFIGURE.md`, `docs/SCHEMA.md`, `docs/RUNBOOK.md` (new), `docs/ARCHITECTURE.md`.
- **Acceptance:** Docs explain configuration recipes, schema reference, runbooks (local/dev/prod), contributing updates.
- **Diffs:** Documentation only.
- **Tests:** `mkdocs build` or `make docs` to ensure formatting.
- **Risk/Rollback:** Low.
- **Effort:** 2 points.

### E2. Developer Playbook & Examples
- [ ] **Status:** Not started
- **Files:** `examples/retail_pack.yaml`, `examples/healthcare_pack.yaml`, `docs/CONTRIBUTING.md` updates.
- **Acceptance:** Example packs load via validator; contributing guide outlines PR process, test expectations, review checklist.
- **Diffs:** New example metadata + doc updates.
- **Tests:** `python -m metadata_cli validate examples/retail_pack.yaml` etc.
- **Risk/Rollback:** Low.
- **Effort:** 2 points.

---

## Sprint 3 Outcomes (Completed)
- [x] Dialect macro registry loads Snowflake and SQLite templates via the metadata runtime (Story A3-001).
- [x] Datasource factory now brokers Snowflake/SQLite connections with health checks and retries (Story C1-002).
- [x] Query compiler binds filters, renders macros, and drives datasource execution (Story C2-003).
- [x] Metadata runtime switch now gates the Streamlit app behind the `USE_METADATA` flag with parity fallbacks (Story D2-004).
- [x] Canonical telco metadata pack and docs aligned to the generated SQLite views, eliminating missing-column/table errors in Streamlit.

## Sprint 4 Plan (In Progress - Vertical Slice)
- **Objective:** Ship a production-ready metadata runtime slice that caches KPI results, auto-generates the telco pack, and proves UI parity end-to-end.
- **Scope (Stories):**
  - **C3 – Caching Policy & Invalidation:** Implement TTL-aware cache module wired into `MetadataDataProvider` and expose CLI hooks for cache inspection/clear.
  - **D1 – Auto-Generate Telco Metadata:** Deliver `tools/generate_telco_metadata.py` that produces the pack consumed by the runtime, with diff review automation.
  - **D3 – Visual Parity Verification:** Add screenshot/DOM diff harness covering all subject areas using the metadata runtime.
  - **E2 – Developer Playbook & Examples:** Publish example packs plus contributor guidance aligned with the new tooling.
- **Working Software Slice:** Metadata runtime uses caching + generated pack, passes visual parity, and ships with updated docs/examples so teams can extend it immediately.

### Sprint 4 Evaluation Checklist
1. `pytest tests/data/test_cache.py -q` (or equivalent) passes, confirming cache hit/miss and invalidation behaviour.
2. `python tools/generate_telco_metadata.py --output metadata/dashboard_telco.yaml --validate` completes with zero diffs after regeneration.
3. `pytest tests/visual/test_visual_parity.py -m visual` produces green screenshots/DOM diffs for every subject area.
4. `python -m metadata_cli validate metadata/dashboard_telco.yaml` validates the regenerated pack with caching enabled.
5. `USE_METADATA=true streamlit run app.py` smoke run confirms cached data + generated pack render without regressions (document test evidence in Sprint 4 evaluation log).
6. Docs/examples lint/build succeed (`mkdocs build` or `make docs`).

## Dependencies & Timeline
- Epics A and C begin immediately (schema + data backend). B depends on A (needs validated metadata). D depends on A–C for runtime readiness. E can proceed in parallel once schema stabilizes.
- Target timeline: 4 sprints (8 weeks). Sprint 1: A + partial C, Sprint 2: remaining C + B, Sprint 3: runtime enablement (D2) + data plumbing (A3/C1/C2), Sprint 4: caching, pack generation, visual parity, and developer enablement.

## Rollback Playbook
- If metadata runtime causes regressions, toggle `USE_METADATA=false` and redeploy legacy build.
- Revert metadata YAML changes by checking out previous git tag (packs are versioned).
- CLI regressions: ship patched release with entry-point disabled; fallback to legacy manual scripts.
