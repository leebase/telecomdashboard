# Sprint 3 Backlog – Metadata Runtime

Use this backlog to track Sprint 3 stories aligned with the refactor plan. Each item references the acceptance criteria defined in `docs/refactor/SPRINT3_PLAN.md`.

## Story A3-001 – Dialect Macro Registry
- **Objective:** Implement dialect-specific macro registry and base SQL templates for Snowflake and SQLite.
- **Acceptance Criteria:**
  1. Macro loader resolves templates from `src/metadata/dialects/` and exposes substitution functions.
  2. Unit tests (`tests/metadata/test_dialects.py`) cover date truncation, QUALIFY emulation, and LIMIT syntax for both dialects.
  3. Failing to find a macro raises a descriptive error pointing to the dialect + macro name.
- **Definition of Done:** Code merged with tests passing; documentation updated if CLI surface changes.

## Story C1-002 – Datasource Factory Abstraction
- **Objective:** Replace direct DB access with a metadata-aware datasource factory supporting Snowflake and SQLite.
- **Acceptance Criteria:**
  1. New `src/data/datasource.py` exposes a factory that returns datasource instances based on metadata configuration.
  2. Datasource instances implement health checks, retry logic, and structured logging.
  3. `database_connection.py` (or equivalent integration point) delegates to the factory when metadata mode is enabled.
  4. Unit tests (`tests/data/test_datasource.py`) mock connection objects and assert retry/health behaviour.

## Story C2-003 – Query Compiler & Filter Binding
- **Objective:** Introduce a metadata-driven query compiler that binds filters and renders SQL via macros.
- **Acceptance Criteria:**
  1. `src/data/query_compiler.py` merges global + KPI filters, binds parameters safely, and renders SQL strings.
  2. Compiler integrates with the macro registry and logs compiled SQL with correlation ids.
  3. Metadata provider calls the compiler before executing datasource queries, returning pandas DataFrames.
  4. Unit tests (`tests/data/test_query_compiler.py`) assert correct SQL output for sample filters.

## Story D2-004 – Feature Flag Runtime Switch
- **Objective:** Expose the metadata runtime behind a top-level `USE_METADATA` flag in the primary dashboard apps.
- **Acceptance Criteria:**
  1. `app.py`, `runAgentsApp.py`, and config loaders include a boolean flag controlling metadata rendering.
  2. When the flag is `False`, the legacy dashboard renders unchanged; when `True`, metadata-driven layout loads.
  3. Automated tests (`tests/ui/test_runtime_switch.py`) cover both code paths.
  4. Documentation (`docs/refactor/CONFIGURE.md`) explains enabling/disabling the flag and any required environment variables.

Track progress during sprint planning by updating each section with status, owners, and notes.
