# Sprint 1 Plan – Metadata Runtime

## Sprint Goal
Establish the metadata runtime foundation so contributors can validate domain packs and see the meta dashboard loading subject areas from YAML. The sprint concludes with CLI tooling, runtime loading, and a stub UI driven by metadata.

## Scope & Deliverables
- **A1 – Metadata Domain Models (Pydantic)**
  - Implement `src/metadata_runtime/models.py` with Pydantic models covering globals, dialects, data_sources, filters, subject_areas, kpis, auxiliary_metrics, widgets, security, refresh.
  - Unit tests in `tests/metadata/test_models.py` verifying validation success/failure paths.
- **A2 – YAML Loader & Validation CLI**
  - Create `src/metadata_runtime/loader.py` to parse YAML, apply defaults, and cache the domain graph.
  - Build `metadata_cli validate <file>` entry point with actionable error reporting.
  - Tests in `tests/metadata/test_loader.py` covering happy path and error surfacing.
- **Meta App Bootstrap**
  - Scaffold `apps/meta/app.py` (or equivalent) that reads metadata once at startup, caches it, and renders tab navigation based on `subject_areas`. Tab bodies can display placeholder text referencing the subject area title.
  - Include configuration handling for `dashboard_telco.yaml` path and feature flag hook for future integration.
- **Docs & Demos**
  - Update `README.md` or `docs/CONFIGURE.md` with instructions: run `metadata_cli validate`, run `streamlit run apps/meta/app.py`.
  - Add `SPRINT1_DEMO.md` (optional) summarizing how to demonstrate the slice.

## Definition of Done
- Running `python -m metadata_cli validate metadata/dashboard_telco.yaml` succeeds and fails appropriately when given an invalid pack.
- `streamlit run apps/meta/app.py` displays tabs named from metadata (Network Performance, Customer Experience, etc.) and confirms metadata is only loaded once per session (log message or counter).
- New unit tests pass via `pytest tests/metadata -v`.
- Repository docs describe the new CLI and stub app usage.

## Out of Scope (Future Sprints)
- Rendering real KPI cards or charts.
- Dialect macro engine, query compilation, or data source abstractions.
- Feature flag integration inside the legacy app.
- Visual regression tooling.

## Next Sprint Candidates
- Implement widget registry + layout interpreter prototype (Epic B1/B2).
- Build query compiler + datasource abstraction (Epic C1/C2) to fetch real data via metadata.
- Introduce caching policy metadata handling (Epic C3).
- Begin automated metadata generation tooling (Epic D1).

## Success Metrics
- Stakeholders can validate metadata packs locally within seconds.
- Meta app stub demonstrates metadata-driven navigation (proof for future UI work).
- Tests covering the new components run in CI (`pytest tests/metadata`).
- No regressions to the legacy dashboard (flag not yet hooked in, but existing app unaffected).

## Sprint Review Checklist
1. Demo CLI validation with both success and failure cases.
2. Demo Streamlit stub showing tabs sourced from YAML.
3. Review unit test coverage report for metadata models/loader.
4. Capture feedback on CLI ergonomics and metadata loading API for use in Sprint 2.
