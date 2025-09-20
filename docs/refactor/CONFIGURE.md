# Configure the Metadata Runtime

## Prerequisites
- Python environment with `poetry`/`pip` deps installed (future CLI will expose `metadata` commands).
- Access to the target metadata pack (e.g., `metadata/dashboard_telco.yaml`).
- Snowflake credentials stored in environment (`SNOWFLAKE_DSN`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_WAREHOUSE`, etc.).
- Optional SQLite cache located at `./data/telecom_db.sqlite` (auto-created when running legacy app).

### Sprint 3 Environment Prep
- Create a `.env.metadata` (or update your secrets manager entry) with:
  - `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_ROLE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`.
  - `SQLITE_DB_PATH` pointing to a writable location (default `data/telecom_metadata.sqlite`).
- Export `USE_METADATA=false` by default so the legacy dashboard remains active until Sprint 3 work is verified.
- Install any new dependencies required by the datasource stack:
  ```bash
  pip install snowflake-connector-python==3.*
  pip install sqlalchemy==2.*
  ```
- For local integration tests, seed the SQLite database with fixture tables via `python metadata/tools/seed_sqlite.py` (provided in Sprint 3).
- Capture credentials in `docs/refactor/INVENTORY.md` if additional secrets are introduced.

## Validate Changes
```bash
# Validate schema & references (exits non-zero on failure)
python -m metadata_cli validate metadata/dashboard_telco.yaml

# Quiet mode suppresses success output for scripting
python -m metadata_cli validate metadata/dashboard_telco.yaml --quiet

# JSON output is helpful in CI or editor integrations
python -m metadata_cli validate metadata/dashboard_telco.yaml --json
```

## Run the Metadata Stub App
```bash
# Optional: point to a different metadata file
export DASHBOARD_METADATA_PATH=/path/to/pack.yaml

# Launch the metadata-driven Streamlit stub
streamlit run apps/meta/app.py
```
The stub loads metadata once per session and now renders the **Network Performance** tab through the widget registry and layout interpreter. KPI cards and the latency chart pull deterministic stub data from the metadata-aware provider. Remaining tabs still display placeholder copy until their layouts migrate in Sprint 3.

## Change a KPI
1. Open the pack file and locate the KPI block (`kpis[]`).
2. Update labels, thresholds, or SQL inside the metric. Example to adjust latency threshold:
   ```yaml
   thresholds:
     good: "<= 40"
     warn: "<= 60"
     bad: "> 60"
   ```
3. If you add new fields to the SELECT list, ensure matching widget encodings (`widgets.secondary[].encoding`).
4. Re-run validation (`python -m metadata_cli validate ...`).
5. Commit changes with rationale in git and tag the pack version.

## Add a Subject Area
1. Define filters under `filters.subject_area.<id>` if needed.
2. Append a new block to `subject_areas[]` with layout sections (12-column grid). Reference existing or new KPI IDs.
3. Create KPI definitions in `kpis[]` referencing the new subject area.
4. Update `security.roles` to expose the subject area to appropriate audiences.
5. Validate the pack; capture UI snapshot via the meta app stub (see below) until automated tooling lands.

## Switch Data Source
1. Add or modify entries in `data_sources`. Example to point Snowflake to staging:
   ```yaml
   data_sources:
     snowflake_main:
       dialect: snowflake
       dsn_env: SNOWFLAKE_STAGING_DSN
       role: ANALYST
       warehouse: KPI_WH_STAGING
   ```
2. Ensure any SQLite caches reference valid paths (set `read_only: true` to prevent writes in prod).
3. Re-run validations; ensure downstream integration tests cover the new connection details.

## Add a New Industry Pack
1. Copy `metadata/dashboard_telco.yaml` to `metadata/packs/<industry>.yaml`.
2. Replace `pack_id`, `label`, and subject area definitions with industry-specific content.
3. Update `data_sources` to point at the new warehouse/schema.
4. Adjust KPIs while preserving required fields (owner, thresholds, widgets, refresh).
5. Validate, generate snapshots via the meta app, and register the pack in this document.

## Operator Runbook Shortcuts
- Toggle metadata runtime using feature flag (`USE_METADATA=true`) once implemented; fallback to legacy if flag unset.
- Clear caches with `python -m metadata_cli validate path --quiet` (validation reloads the metadata cache automatically).
- Deploy pack updates by bundling YAML + changelog; runtime reloads metadata on restart or via `metadata_cli reload` API.

## Open Items
- CLI command names may evolve during implementation; finalize in Epic A tasks.
- Decide whether benchmark management remains separate UI or becomes metadata-driven widget.
- Document secret rotation playbook once Snowflake adapter finalized.
