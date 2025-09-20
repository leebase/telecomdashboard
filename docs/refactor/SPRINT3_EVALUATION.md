# Sprint 3 Evaluation Guide

Use this checklist to validate Sprint 3 deliverables before promoting the metadata runtime behind the production flag.

## Prerequisites
- Virtual environment with project dependencies installed (include any new Snowflake/SQLite drivers from Sprint 3).
- Access to the `metadata-runtime` branch with Sprint 3 changes.
- Database credentials or fixtures for the configured datasource targets (SQLite file checked in; Snowflake creds via env vars if applicable).

## 1. Run Regression Tests
```bash
pytest tests/metadata -q
pytest tests/data -q
pytest tests/ui/test_runtime_switch.py -q
```
- Metadata suite confirms schema/loader stability.
- Data suite exercises the datasource factory and query compiler paths (use `-m integration` if optional integration tests are provided).
- Runtime-switch test verifies both legacy and metadata modes.

## 2. Validate Dialect Macros
```bash
pytest tests/metadata/test_dialects.py -q
```
- Confirms macro substitutions for date truncation, QUALIFY emulation, and LIMIT logic.

## 3. CLI Validation Still Passes
```bash
python -m metadata_cli validate metadata/dashboard_telco.yaml
```
- Expect exit code 0 and no warnings. Investigate any new validation errors before continuing.

## 4. Manual Datasource Smoke Test
- Launch an interactive Python shell or notebook and instantiate `MetadataDataProvider` with the Sprint 3 metadata pack.
- Call `provider.get_metric_frame("metric_network_latency")` and confirm a DataFrame is returned (stub fallback is acceptable if Snowflake is unavailable).
- Inspect logs (or Streamlit console) to ensure compiled SQL statements are emitted when datasources respond.

## 5. Feature Flag Runtime Switch
1. Launch the legacy experience (flag off):
   ```bash
   streamlit run app.py
   ```
   - Verify the original dashboard renders (no metadata logs).
2. Enable metadata mode (e.g., `export USE_METADATA=true` or toggle in config), then rerun Streamlit.
   - Confirm subject areas, KPI cards, and charts load via datasource-backed metadata.
   - Check logs for compiler output and datasource health messages.

## 6. Snowflake Connectivity (Optional but Recommended)
```bash
pytest tests/data/test_datasource.py -m snowflake
```
- Runs only if Snowflake credentials are provided. Skip with confidence if not available in the environment.

## 7. Documentation Spot Check
- `docs/refactor/CONFIGURE.md`: includes datasource setup and flag instructions.
- `docs/refactor/SPRINT3_PLAN.md`: matches what shipped.
- `docs/refactor/REFACTOR_PLAN.md`: statuses for A3, C1, C2, and D2 marked complete.

## Exit Criteria
Sprint 3 is complete when:
- All new/updated automated tests pass locally (metadata, data, runtime switch, dialects).
- Metadata CLI validation continues to succeed on the canonical pack.
- The datasource factory returns real data (or deterministic fixtures) through the metadata runtime.
- Streamlit app runs in both legacy and metadata modes via the feature flag without errors.
- Documentation reflects the new data stack and operational steps.

Capture any issues (e.g., slow SQL compilation, flaky Snowflake connections, missing logging context) and convert them into backlog items for Sprint 4.
