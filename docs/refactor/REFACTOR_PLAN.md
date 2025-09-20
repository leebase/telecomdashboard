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
- [x] **Status:** Completed (Sprint 4 TTL-aware cache module with SQLite persistence)
- **Files:** `src/data/cache.py`, integrated with `MetadataDataProvider`.
- **Acceptance:** Cache respects metadata TTL, keyed by KPI + filters, supports SQLite materialized cache optional.
- **Diffs:** New cache module + CLI `metadata_cli cache clear/stats` commands.
- **Tests:** `pytest tests/data/test_cache.py`.
- **Risk/Rollback:** Low—flagged usage. Rollback by disabling metadata cache call.
- **Effort:** 3 points.

---

## Epic D – Migration & Compatibility

### D1. Inventory & Auto-Generate Telco Metadata
- [x] **Status:** Completed (Sprint 4 auto-generate script with validation)
- **Files:** `tools/generate_telco_metadata.py`, `metadata/dashboard_telco.yaml` (output of this pass).
- **Acceptance:** Script validates and regenerates existing metadata pack with generation metadata.
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
- [x] **Status:** Completed (Sprint 4 visual parity harness structure)
- **Files:** `tests/visual/test_visual_parity.py`, baseline assets under `tests/visual/baseline/`.
- **Acceptance:** Test framework for screenshot/DOM comparison per subject area with tolerance settings.
- **Diffs:** Visual test harness, baseline creation support.
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
- [x] **Status:** Completed (Sprint 4 example packs and contributing updates)
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

## Sprint 4 Outcomes (Completed)
- [x] Implemented TTL-aware cache module with SQLite persistence and CLI hooks (Story C3-001).
- [x] Created auto-generate script for telco metadata pack with validation (Story D1-002).
- [x] Built visual parity verification harness with screenshot/DOM comparison structure (Story D3-003).
- [x] Developed example packs for retail and healthcare industries with updated contributing docs (Story E2-004).
- [x] Added cache management methods to MetadataDataProvider and CLI commands for inspection/clearing.
- [x] Ensured multi-database support baked in with SQLite prioritization for development.

## Sprint 5 Outcomes (Completed)
- [x] **Snowflake Integration:** Full Snowflake datasource implementation with connection pooling and query tagging.
- [x] **Complete Visual Parity:** Implemented headless screenshot comparison and DOM diffing for all subject areas.
- [x] **Enterprise Features:** Added authentication, audit logging, and production monitoring.
- [x] **Performance Optimization:** Query optimization, async processing, and load testing framework.
- [x] **Documentation Finalization:** Complete deployment guides, troubleshooting docs, and configuration.
- **Sprint 5 Evaluation Checklist (Completed):**
  1. ✅ `pytest tests/data/test_datasource.py -m snowflake` passes with real Snowflake connection.
  2. ✅ `pytest tests/visual/test_visual_parity.py -m visual` achieves <2% difference across all tabs.
  3. ✅ `USE_METADATA=true streamlit run app.py` runs in production mode with all features.
  4. ✅ Documentation builds successfully and covers all deployment scenarios.
  5. ✅ Load testing shows acceptable performance under concurrent users.

## Sprint 6 Plan (New - Data Abstraction Layer)
- **Objective:** Implement a view abstraction layer to ensure no direct table queries, facilitating client data integration and providing clean separation between physical and logical data models.
- **Scope (Stories):**
  - **V1 – View Layer Design:** Create standardized view definitions for all telecom data tables with initial "SELECT * FROM table" implementations.
  - **V2 – View Implementation:** Implement views in both SQLite (development) and Snowflake (production) databases.
  - **V3 – Metadata Integration:** Update metadata pack to reference views instead of direct tables.
  - **V4 – Migration Strategy:** Provide scripts to create views and update existing queries seamlessly.
  - **V5 – Testing & Validation:** Ensure view layer works correctly with existing functionality and performance.
- **Working Software Slice:** Metadata runtime queries views exclusively, enabling seamless client data integration without code changes.
- **Sprint 6 Evaluation Checklist:**
  1. `python scripts/create_views.py` successfully creates all required views in SQLite.
  2. `python scripts/create_views.py --snowflake` creates equivalent views in Snowflake.
  3. `python -m metadata_cli validate metadata/dashboard_telco.yaml` passes with view references.
  4. `USE_METADATA=true streamlit run app.py` renders correctly using view-based queries.
  5. Performance benchmarks show no degradation when using views vs direct tables.

## Dependencies & Timeline
- Epics A and C begin immediately (schema + data backend). B depends on A (needs validated metadata). D depends on A–C for runtime readiness. E can proceed in parallel once schema stabilizes. V (View Layer) depends on C (data layer completion).
- Target timeline: 6 sprints (12 weeks). Sprint 1: A + partial C, Sprint 2: remaining C + B, Sprint 3: runtime enablement (D2) + data plumbing (A3/C1/C2), Sprint 4: caching, pack generation, visual parity, and developer enablement, Sprint 5: enterprise features and production readiness, Sprint 6: view abstraction layer for client data integration.

## Future Enhancements (Sprint 7+)

### Sprint 7 – Advanced Analytics & AI
- **AI-001:** Implement advanced AI insights with ML model integration
- **AI-002:** Add predictive analytics and forecasting capabilities
- **AI-003:** Create anomaly detection for KPI trends
- **AI-004:** Implement natural language query processing
- **AI-005:** Add automated report generation with AI summaries

### Sprint 8 – Multi-Tenant Architecture
- **MT-001:** Implement tenant isolation at database level
- **MT-002:** Add tenant-specific metadata packs
- **MT-003:** Create tenant management and provisioning system
- **MT-004:** Implement cross-tenant analytics and reporting
- **MT-005:** Add tenant-specific security policies and RBAC

### Sprint 9 – Advanced Performance & Scaling
- **PERF-001:** Implement query result caching with Redis
- **PERF-002:** Add database connection pooling optimization
- **PERF-003:** Create horizontal scaling with load balancers
- **PERF-004:** Implement read replicas and query routing
- **PERF-005:** Add performance monitoring and alerting

### Sprint 10 – API Ecosystem & Integration
- **API-001:** Create REST API for external KPI access
- **API-002:** Implement webhook system for real-time updates
- **API-003:** Add GraphQL API for flexible queries
- **API-004:** Create SDKs for common programming languages
- **API-005:** Implement OAuth 2.0 and API key management

### Sprint 11 – Mobile & Responsive Design
- **MOBILE-001:** Create responsive mobile dashboard
- **MOBILE-002:** Implement PWA capabilities
- **MOBILE-003:** Add offline data synchronization
- **MOBILE-004:** Create mobile-specific KPI visualizations
- **MOBILE-005:** Implement touch-optimized interactions

### Sprint 12 – Compliance & Governance
- **GOV-001:** Implement GDPR compliance features
- **GOV-002:** Add SOC 2 audit trail enhancements
- **GOV-003:** Create data retention and deletion policies
- **GOV-004:** Implement data export and portability features
- **GOV-005:** Add compliance reporting and certification support

## Rollback Playbook
- If metadata runtime causes regressions, toggle `USE_METADATA=false` and redeploy legacy build.
- Revert metadata YAML changes by checking out previous git tag (packs are versioned).
- CLI regressions: ship patched release with entry-point disabled; fallback to legacy manual scripts.
