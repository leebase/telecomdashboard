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
- **Files:** `src/metadata/models.py`, `src/metadata/__init__.py`.
- **Acceptance:** Models cover all schema fields (globals, dialects, data_sources, filters, subject_areas, kpis, security, refresh). Validation errors emit actionable messages.
- **Diffs:** New module; unit tests in `tests/metadata/test_models.py`.
- **Tests:** `pytest tests/metadata/test_models.py`.
- **Risk/Rollback:** Low—new files only; delete module if blocking.
- **Effort:** 3 points.

### A2. YAML Loader & Validator CLI
- **Files:** `src/metadata/loader.py`, `src/cli/metadata_cli.py`, `pyproject` entry point.
- **Acceptance:** CLI `metadata_cli validate <file>` parses YAML, applies models, prints summary + line references.
- **Diffs:** Loader, CLI, wiring in `setup.cfg`/`pyproject.toml`.
- **Tests:** `pytest tests/metadata/test_loader.py` with fixture YAMLs.
- **Risk/Rollback:** Medium—CLI wiring may break packaging. Rollback by disabling console entry point.
- **Effort:** 3 points.

### A3. Dialect Macro System Design & Stubs
- **Files:** `src/metadata/dialects/__init__.py`, `macros/snowflake.sql`, `macros/sqlite.sql`, `tests/metadata/test_dialects.py`.
- **Acceptance:** Macro registry loads per dialect; rendering stub returns compiled SQL string; tests assert macro substitution for date trunc, QUALIFY emulation, limit syntax.
- **Diffs:** New macro files + unit tests.
- **Tests:** `pytest tests/metadata/test_dialects.py`.
- **Risk/Rollback:** Low; revert new module if necessary.
- **Effort:** 2 points.

---

## Epic B – Widget Registry & Layout Interpreter

### B1. Widget Registry Mapping
- **Files:** `src/ui/metadata_widgets.py`, update `kpi_components.py` to expose registry-friendly functions.
- **Acceptance:** Registry maps metadata `type` values (`kpi_card`, `timeseries_line`, `bar_chart`, `area_chart`, `distribution`, `table`, `benchmark_editor`, `ai_insights_button`) to callable factories; fallbacks log warnings.
- **Diffs:** New registry module + minimal adapters in existing widget helpers (no UX change when flag off).
- **Tests:** `pytest tests/ui/test_widget_registry.py` using fake metadata payloads.
- **Risk/Rollback:** Medium—touches shared UI helpers. Rollback by reverting registry imports and stubs.
- **Effort:** 4 points.

### B2. Layout Interpreter (12-Column Grid)
- **Files:** `src/ui/layout_engine.py`, updates to `app.py` to call interpreter when flag true.
- **Acceptance:** Layout interpreter reads metadata sections → renders Streamlit columns/expanders, supports responsive breakpoints + print mode; unit snapshots confirm structure.
- **Diffs:** New engine + guarded hook in `app.py` (flagged).
- **Tests:** `pytest tests/ui/test_layout_engine.py`; optional headless snapshot via `streamlit testing` harness.
- **Risk/Rollback:** High—touches `app.py`. Rollback by toggling flag to false and reverting hook.
- **Effort:** 5 points.

---

## Epic C – Data Layer & Caching

### C1. DataSource Abstraction & Connection Factory
- **Files:** `src/data/datasource.py`, refactor `database_connection.py` to delegate when flag enabled.
- **Acceptance:** Factory supports Snowflake (via `snowflake-connector-python`) and SQLite; includes health check, retry, circuit breaker (reuse existing logic), connection pooling for Snowflake.
- **Diffs:** New abstraction, minimal integration patch (guarded by flag).
- **Tests:** `pytest tests/data/test_datasource.py` with mocks; integration `pytest tests/integration/test_datasource_runtime.py -m integration`.
- **Risk/Rollback:** Medium—introduces new dependencies. Rollback by disabling metadata path.
- **Effort:** 5 points.

### C2. Query Compilation & Filter Binding
- **Files:** `src/data/query_compiler.py`, updates to `security_manager.py` for parameter whitelisting.
- **Acceptance:** Compiler merges filter state, renders SQL via dialect macros, enforces allow-listed params, logs compiled SQL.
- **Diffs:** New module + security hooks.
- **Tests:** `pytest tests/data/test_query_compiler.py` with golden SQL fixtures.
- **Risk/Rollback:** Medium; rollback by bypassing compiler when flag false.
- **Effort:** 4 points.

### C3. Caching Policy & Invalidation
- **Files:** `src/data/cache.py`, integrate with existing `cache_with_ttl` decorator.
- **Acceptance:** Cache respects metadata TTL, keyed by KPI + filters, supports SQLite materialized cache optional.
- **Diffs:** New cache module + optional CLI `metadata_cli cache clear` command.
- **Tests:** `pytest tests/data/test_cache.py`.
- **Risk/Rollback:** Low—flagged usage. Rollback by disabling metadata cache call.
- **Effort:** 3 points.

---

## Epic D – Migration & Compatibility

### D1. Inventory & Auto-Generate Telco Metadata
- **Files:** `tools/generate_telco_metadata.py`, `metadata/dashboard_telco.yaml` (output of this pass).
- **Acceptance:** Script introspects legacy code (metrics, charts, filters) and emits metadata identical to hand-authored pack; diff is tracked and reviewed.
- **Diffs:** New tooling; YAML lives in repo.
- **Tests:** `pytest tests/tools/test_generate_telco_metadata.py` comparing sample output to fixture.
- **Risk/Rollback:** Low—tooling only. Rollback by removing script.
- **Effort:** 3 points.

### D2. Feature Flag Integration & Runtime Switch
- **Files:** `app.py`, `runAgentsApp.py`, `config_manager.py`.
- **Acceptance:** Config exposes `USE_METADATA`; when true, tabs render from metadata; fallback path still available. Logging indicates active mode.
- **Diffs:** Conditional branches + new config field.
- **Tests:** `pytest tests/ui/test_runtime_switch.py`; manual smoke `streamlit run app.py` both modes.
- **Risk/Rollback:** High—UI entry point touched. Rollback by setting flag false; revert merge if needed.
- **Effort:** 4 points.

### D3. Visual Parity Verification
- **Files:** `tests/visual/test_visual_parity.py`, baseline assets under `tests/visual/baseline/`.
- **Acceptance:** Headless renderer captures screenshots/DOM snapshots per subject area; comparison tolerance ≤2%.
- **Diffs:** Visual test harness, baseline assets.
- **Tests:** `pytest tests/visual/test_visual_parity.py -m visual`.
- **Risk/Rollback:** Medium—visual tests brittle. Rollback by quarantining marker.
- **Effort:** 3 points.

---

## Epic E – Documentation & Examples

### E1. Operator & Extender Docs
- **Files:** `docs/CONFIGURE.md`, `docs/SCHEMA.md`, `docs/RUNBOOK.md` (new), `docs/ARCHITECTURE.md`.
- **Acceptance:** Docs explain configuration recipes, schema reference, runbooks (local/dev/prod), contributing updates.
- **Diffs:** Documentation only.
- **Tests:** `mkdocs build` or `make docs` to ensure formatting.
- **Risk/Rollback:** Low.
- **Effort:** 2 points.

### E2. Developer Playbook & Examples
- **Files:** `examples/retail_pack.yaml`, `examples/healthcare_pack.yaml`, `docs/CONTRIBUTING.md` updates.
- **Acceptance:** Example packs load via validator; contributing guide outlines PR process, test expectations, review checklist.
- **Diffs:** New example metadata + doc updates.
- **Tests:** `python -m metadata_cli validate examples/retail_pack.yaml` etc.
- **Risk/Rollback:** Low.
- **Effort:** 2 points.

---

## Dependencies & Timeline
- Epics A and C begin immediately (schema + data backend). B depends on A (needs validated metadata). D depends on A–C for runtime readiness. E can proceed in parallel once schema stabilizes.
- Target timeline: 3 sprints (6 weeks). Sprint 1: A, partial C. Sprint 2: complete C, B. Sprint 3: D, E, release hardening.

## Rollback Playbook
- If metadata runtime causes regressions, toggle `USE_METADATA=false` and redeploy legacy build.
- Revert metadata YAML changes by checking out previous git tag (packs are versioned).
- CLI regressions: ship patched release with entry-point disabled; fallback to legacy manual scripts.
