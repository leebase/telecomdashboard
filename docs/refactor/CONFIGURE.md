# Configure the Metadata Runtime

## Prerequisites
- Python environment with `poetry`/`pip` deps installed (future CLI will expose `metadata` commands).
- Access to the target metadata pack (e.g., `metadata/dashboard_telco.yaml`).
- Snowflake credentials stored in environment (`SNOWFLAKE_DSN`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_WAREHOUSE`, etc.).
- Optional SQLite cache located at `./data/telecom_db.sqlite` (auto-created when running legacy app).

## Validate Changes
```bash
# Validate schema & references
python -m metadata_cli validate metadata/dashboard_telco.yaml

# Preview compiled SQL for Snowflake vs SQLite
python -m metadata_cli preview --kpi kpi_network_availability --dialect snowflake
python -m metadata_cli preview --kpi kpi_network_availability --dialect sqlite
```

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
4. Run validation and `metadata_cli test --kpi kpi_network_latency` to assert golden CSV outputs.
5. Commit changes with rationale in git and tag the pack version.

## Add a Subject Area
1. Define filters under `filters.subject_area.<id>` if needed.
2. Append a new block to `subject_areas[]` with layout sections (12-column grid). Reference existing or new KPI IDs.
3. Create KPI definitions in `kpis[]` referencing the new subject area.
4. Update `security.roles` to expose the subject area to appropriate audiences.
5. Validate pack and capture UI snapshot via `metadata_cli snapshot --subject-area new_id`.

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
3. Re-run validations; use `metadata_cli healthcheck` to confirm both dialects compile.

## Add a New Industry Pack
1. Copy `metadata/dashboard_telco.yaml` to `metadata/packs/<industry>.yaml`.
2. Replace `pack_id`, `label`, and subject area definitions with industry-specific content.
3. Update `data_sources` to point at the new warehouse/schema.
4. Adjust KPIs while preserving required fields (owner, thresholds, widgets, refresh).
5. Validate, generate snapshots, and register the pack in `docs/CONFIGURE.md` table.

## Operator Runbook Shortcuts
- Toggle metadata runtime using feature flag (`USE_METADATA=true`) once implemented; fallback to legacy if flag unset.
- Clear caches with `metadata_cli cache clear --scope all` before reloads.
- Deploy pack updates by bundling YAML + changelog; runtime reloads metadata on restart or via `metadata_cli reload` API.

## Open Items
- CLI command names may evolve during implementation; finalize in Epic A tasks.
- Decide whether benchmark management remains separate UI or becomes metadata-driven widget.
- Document secret rotation playbook once Snowflake adapter finalized.
