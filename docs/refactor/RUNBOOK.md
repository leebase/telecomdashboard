# Metadata Runtime Runbook

## Environments
| Environment | Branch | Feature Flags | Notes |
|-------------|--------|----------------|-------|
| Local       | feature/metadata-runtime | `USE_METADATA` optional (default false) | Developers toggle flag while iterating.
| Staging     | release-candidate        | `USE_METADATA=true` (side-by-side smoke) | Connected to Snowflake staging DSN.
| Production  | main                     | `USE_METADATA=false` until launch        | Flip flag gradually per cohort.

## Bootstrap
1. Clone repository and create virtualenv.
2. Install dependencies: `pip install -r requirements.txt` (plus Snowflake connector).
3. Ensure `.env` or environment variables export Snowflake credentials:
   ```bash
   export SNOWFLAKE_DSN="account.region"
   export SNOWFLAKE_USER="svc_metadata"
   export SNOWFLAKE_PASSWORD="<secret>"
   export SNOWFLAKE_WAREHOUSE="KPI_WH"
   export SNOWFLAKE_ROLE="ANALYST"
   ```
4. (Optional) Seed SQLite cache: `python load_csv_data.py`.

## Local Workflow
- Validate metadata pack: `python -m metadata_cli validate metadata/dashboard_telco.yaml`.
- Run Streamlit legacy mode: `streamlit run app.py` (flag off).
- Run metadata mode: `USE_METADATA=true streamlit run app.py`.
- Clear caches: `python -m metadata_cli cache clear --scope local`.
- Capture visual snapshots: `pytest tests/visual/test_visual_parity.py -m visual --update-baseline`.

## Deployment Pipeline
1. CI validates packs, runs unit + integration suites, captures snapshots.
2. Staging deploy uses infrastructure flag store (e.g., LaunchDarkly) to turn on metadata runtime for internal users.
3. Monitor Snowflake query latency, cache hit rate, error budgets via telemetry (Grafana dashboards fed from logging).
4. Production rollout toggled via flag; maintain ability to revert within minutes.

## Snowflake Credentials
- Managed by secrets manager (AWS Secrets Manager / Azure KeyVault). Runtime loads DSN + password into environment before process start.
- Rotate quarterly; update environment variable references and redeploy.
- Enforce role-based policies to restrict metadata runtime to read-only tables.

## SQLite Cache
- Location: `./data/telecom_db.sqlite` (local) or `/var/cache/telecom.sqlite` (server).
- Permissions: `chmod 600` owner-only.
- Cache refresh triggered via `metadata_cli cache prime --config metadata/dashboard_telco.yaml` for nightly priming.
- Monitor file size; prune via `metadata_cli cache vacuum` when >1GB.

## Secrets Handling
- `.env` files only for local development; never commit.
- Use `setup_secure_environment.py` to scaffold `.env`, set proper perms, and inject placeholders.
- Telemetry + logs must redact DSN and user info before persisting (handled by `logging_config.py`).

## Incident Response
1. Detect anomaly (latency spike, failed validation).
2. Toggle `USE_METADATA=false` via config service; redeploy to revert to legacy path.
3. Inspect logs filtered by `metadata_runtime` component; check compiled SQL output for failures.
4. Run `metadata_cli validate` on offending pack; compare git history for recent changes.
5. If Snowflake outage, route queries to SQLite cache by updating `data_sources.default` to `sqlite` and reloading pack (temporary workaround).

## Open Items
- Finalize telemetry dashboard definitions (latency, cache hit rate, error rate).
- Document automation for rotating LaunchDarkly flag during rollout.
- Determine RACI for metadata pack approvals (Product vs Data Engineering).
