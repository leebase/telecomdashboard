# Sprint 2 Plan – Metadata Runtime

## Sprint Goal
Deliver a metadata-driven rendering slice that reads real KPI definitions and renders Streamlit components through a widget registry and basic layout interpreter. The sprint concludes with KPI cards and at least one chart rendered via metadata for the Network Performance tab, backed by stubbed data adapters.

## Scope & Deliverables
- **B1 – Widget Registry MVP**
  - Introduce `src/ui/metadata_widgets.py` mapping metadata widget types (`kpi_card`, `timeseries_line`, `bar_chart`) to callable adapters around existing Streamlit helpers.
  - Ensure adapters accept structured payloads (value, delta, formatting) and return rendering callables.
  - Unit tests in `tests/ui/test_widget_registry.py` using fake metadata payloads.
- **B2 – Layout Interpreter (Network Tab only)**
  - Create `src/ui/layout_engine.py` capable of reading a 12-column grid layout for one subject area.
  - Integrate with `apps/meta/app.py` behind a feature flag (`ENABLE_LAYOUT_ENGINE`) defaulting to true in the meta app.
  - Tests in `tests/ui/test_layout_engine.py` verifying layout row/column construction and error handling.
- **C1-lite – Data Adapter Stub**
  - Implement a simple metadata-aware data provider in `src/data/metadata_provider.py` that resolves metric datasets to mocked Pandas DataFrames (built from the generated metadata pack).
  - Provide minimal caching via an in-memory dict keyed by metric ID + filters.
  - Tests in `tests/data/test_metadata_provider.py` covering load and caching behaviour.
- **Meta App Integration**
  - Update `apps/meta/app.py` to: load widgets/layout, fetch data via the provider, render KPI cards + latency line chart for `network_performance` using real metadata definitions.
  - Add CLI switch (`python -m metadata_cli render --subject-area network_performance`) to dry-run the layout and output summary (optional bonus if time allows).
- **Documentation**
  - Document widget registry and layout usage in `docs/refactor/CONFIGURE.md` and add Sprint 2 evaluation criteria in a new `docs/refactor/SPRINT2_EVALUATION.md`.

## Definition of Done
- `streamlit run apps/meta/app.py` renders the Network Performance tab with KPI cards and a latency chart pulled from metadata using the new registry/layout.
- Widget registry and layout engine covered by unit tests (`pytest tests/ui -v`).
- Metadata provider returns deterministic DataFrames and is exercised by tests (`pytest tests/data -v`).
- Documentation updated to describe new commands and architecture sections.
- All existing metadata validation/tests continue to pass (`pytest tests/metadata -v`).

## Non-Goals
- Full data source abstraction for Snowflake/SQLite (covered in Sprint 3).
- Complete layout coverage for all tabs (only Network Performance required this sprint).
- Visual regression tooling.
- Feature flag wiring in the legacy app.

## Risks & Mitigations
- **Complex layout logic** → limit scope to single tab; add TODOs for future responsiveness.
- **Data provider realism** → use deterministic stub data, documenting where real query compilation will plug in.
- **Regression risk** → keep registry/layout guarded behind meta app path; legacy app untouched.

## Next Sprint Candidates (Sprint 3)
- Expand data provider into real query compiler + datasource abstraction (Epic C1/C2).
- Extend layout interpreter to all tabs and add responsive breakpoints.
- Implement caching policy metadata (Epic C3) and CLI cache commands.

## Sprint Review Checklist
1. Demo Streamlit meta app showing metadata-driven KPI cards + chart for Network tab.
2. Review new unit test suites (UI/data) and confirm coverage.
3. Walk through documentation updates highlighting registry/layout usage.
4. Capture feedback for scaling to other tabs and real data sources.
