# Sprint 2 Evaluation Guide

## Prerequisites
- Metadata runtime branch checked out (`metadata-runtime`).
- Virtual environment with dependencies installed, including `pytest`, `pydantic`, `pandas`, and `streamlit`.
- Sprint 2 deliverables pulled locally.

## 1. Run Metadata Tests
```bash
pytest tests/metadata -q
```
Expect all tests to pass (regression guard from Sprint 1).

## 2. Run New UI & Data Tests
```bash
pytest tests/ui -q
pytest tests/data -q
```
- `tests/ui` validates widget registry and layout interpreter behaviour.
- `tests/data` verifies the metadata data provider emits deterministic data.

## 3. Validate Metadata Pack
```bash
python -m metadata_cli validate metadata/dashboard_telco.yaml
```
- Exit code `0` indicates the pack remains valid.
- If validation fails, review the error list, fix the metadata, and rerun.

## 4. Launch the Meta App
```bash
streamlit run apps/meta/app.py
```
- Confirm the **Network Performance** tab renders KPI cards with values/deltas and the latency trend chart.
- Use the sidebar to verify metadata pack details.
- Navigate to other tabs and note the placeholder messaging (expected for Sprint 2).

## 5. Regression Checks
- Toggle `DASHBOARD_METADATA_PATH` to a modified pack and ensure the app reloads values accordingly.
- Refresh the page to confirm metadata caching behaviour (no repeated load log entries unless file changes).

## 6. Documentation Spot Check
- `docs/refactor/CONFIGURE.md`: includes updated guidance for the widget registry/layout.
- `docs/refactor/SPRINT_PLAN.md`: reflects Sprint 2 scope.
- `docs/refactor/REFACTOR_PLAN.md`: statuses updated for Epics B1/B2 and C1-lite.

## Exit Criteria
Sprint 2 is successful when:
1. Widget registry and layout interpreter tests pass.
2. The metadata-driven meta app renders Network Performance cards + chart from metadata.
3. Metadata validation remains successful.
4. Documentation and evaluation guide reference the new runtime components.

Capture any feedback (e.g., desired widget types, chart variations, data realism) to feed into Sprint 3 planning, where the datasource abstraction and remaining tabs will be implemented.
