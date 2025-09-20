# Sprint 1 Evaluation Guide

Use this checklist to verify Sprint 1 outcomes and capture feedback for Sprint 2.

## Prerequisites
- Python virtual environment with dependencies installed (`pip install -r requirements.txt`).
- Access to the metadata branch (`metadata-runtime`).

## 1. Validate the Metadata Pack
```bash
python -m metadata_cli validate metadata/dashboard_telco.yaml
```
- ✅ Passes with exit code 0 → Continue.
- ❌ Fails → Review error list, confirm diagnostics are actionable (field path + message).

## 2. Break the Pack Intentionally
```bash
# Example: remove a required data source reference
python - <<'PY'
import yaml
from pathlib import Path
path = Path("metadata/dashboard_telco.yaml")
config = yaml.safe_load(path.read_text())
config["kpis"][0]["metrics"][0]["data_source"] = "missing"
path.write_text(yaml.safe_dump(config))
PY

python -m metadata_cli validate metadata/dashboard_telco.yaml --json
```
- Confirm non-zero exit code.
- Ensure JSON payload highlights the failing field (e.g., `kpis.0.metrics.0.data_source`).
- Revert the file after the test (`git checkout -- metadata/dashboard_telco.yaml`).

## 3. Launch the Metadata Stub App
```bash
streamlit run apps/meta/app.py
```
- Verify the page title reads **Metadata-Driven Dashboard Stub**.
- Confirm subject-area tabs match the metadata order (Network Performance, Customer Experience, etc.).
- Each tab should list its KPIs and show placeholder text about future widget integration.
- Sidebar displays pack metadata (pack id, schema, app version, data sources).

## 4. Cache Behavior
- Refresh the Streamlit page; confirm no errors and metadata reload message remains green.
- Optionally, update the YAML file while the app is running, then refresh. Cached view should reflect changes because Streamlit reruns the script (lru cache invalidated when process restarts).

## 5. Automated Tests
```bash
pytest tests/metadata -v
```
- All tests should pass, covering models, loader caching, and CLI behavior.

## 6. Documentation Spot Check
- `docs/refactor/CONFIGURE.md`: contains new validation and stub app instructions.
- `docs/refactor/SPRINT_PLAN.md`: scope matches delivered features; update statuses if necessary.

## Exit Criteria
Sprint 1 is successful when:
- CLI validation succeeds on the canonical pack and fails with actionable errors on malformed packs.
- Metadata-driven Streamlit stub renders subject areas from YAML without manual wiring.
- Tests in `tests/metadata` pass locally and in CI.
- Documentation explains how to validate and preview packs.

Capture any gaps or frustrations encountered during evaluation and feed them into Sprint 2 planning (e.g., desire for SQL preview tooling, additional CLI commands, or more robust caching controls).
