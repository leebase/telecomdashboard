# Sprint 3 Plan – Metadata Runtime

## Sprint Goal
Enable the metadata runtime to fetch real KPI data through the new data abstraction stack and expose the experience behind a production-ready feature flag in the primary dashboard. Sprint 3 completes the core data pipeline (dialect macros, query compilation, and datasource factory) and wires it into the live app while keeping rollback safe.

## Scope & Deliverables
- **A3 – Dialect Macro System**
  - Implement macro registry and placeholder SQL templates for Snowflake and SQLite.
  - Add tests (`tests/metadata/test_dialects.py`) covering substitution of date truncation, QUALIFY, and LIMIT semantics.
- **C1 – DataSource Abstraction & Connection Factory**
  - Create `src/data/datasource.py` with pluggable implementations for Snowflake and SQLite.
  - Update `database_connection.py` (behind feature flag) to use the factory and include health checks.
  - Unit tests with mocks (`tests/data/test_datasource.py`) plus optional integration marker for SQLite.
- **C2 – Query Compiler & Filter Binding**
  - Build `src/data/query_compiler.py` that merges metadata filters, applies macros, and generates SQL.
  - Update metadata provider to call the compiler and return DataFrames from the datasource.
  - Tests (`tests/data/test_query_compiler.py`) using golden SQL fixtures and filter scenarios.
- **D2 – Feature Flag Integration & Runtime Switch**
  - Introduce `USE_METADATA` flag in `app.py`, `runAgentsApp.py`, and configuration loaders.
  - Ensure metadata-driven tabs render when the flag is true and legacy path remains default.
  - Add regression tests (`tests/ui/test_runtime_switch.py`) validating both code paths.
- **Documentation & Ops**
  - Expand `docs/refactor/CONFIGURE.md` with datasource setup and feature flag instructions.
  - Record Sprint 3 acceptance criteria in `docs/refactor/SPRINT3_EVALUATION.md`.

## Definition of Done
- `python -m metadata_cli validate metadata/dashboard_telco.yaml` still succeeds.
- `pytest tests/metadata -v`, `pytest tests/data -v`, and `pytest tests/ui/test_runtime_switch.py -v` all pass with new suites.
- `streamlit run app.py` renders legacy dashboard by default and metadata-driven version when `USE_METADATA=true`.
- Datasource factory and query compiler log structured messages for tracing compiled SQL and connection usage.

## Out of Scope (Next Sprints)
- C3 caching policy engine and CLI commands.
- Automated metadata generation tooling (Epic D1).
- Visual regression capture (Epic D3).
- Responsive layout enhancements or additional widget types beyond current registry.

## Risks & Mitigations
- **Snowflake connectivity complexity** → start with SQLite integration tests; guard Snowflake paths with feature toggles and stub credentials.
- **SQL injection/parameter safety** → enforce allow-listed parameters in compiler and add security unit tests.
- **Flag rollout risk** → default flag to false; include smoke checklist for both modes.

## Ready Backlog for Sprint 4
- Implement caching policy module (C3) and CLI cache controls.
- Build metadata generation script for telco pack (D1).
- Add visual parity harness and baseline assets (D3).
- Extend layout interpreter to customer experience tab with responsive tweaks.
