# Metadata Schema Specification

## Purpose
Defines the authoritative YAML schema that drives the metadata runtime (schema version 1.0). The schema is validated via Pydantic models and JSON Schema; every pack must conform before deployment.

## Top-Level Structure
```yaml
schema_version: 1.0            # SemVer, locked by runtime
app_version: 0.9.0             # UI/runtime release the pack targets
pack_id: telecom_default       # Domain pack identifier
label: Telecom KPI Dashboard   # Friendly name
globals:
  timezone: America/Chicago
  default_date_range: last_30_days
  currency: USD
  theme: cognizant_dark
  print_mode_enabled: false
  ai_insights_enabled: true

# Dialect definitions + default selection

```

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `schema_version` | string | ✅ | Must match runtime major.minor.
| `app_version` | string | ✅ | Compatible runtime version (SemVer range allowed).
| `pack_id` | string | ✅ | Unique slug (`[a-z0-9_]+`).
| `label` | string | ✅ | Human-readable pack name.
| `globals` | map | ✅ | App-level settings; see below.
| `dialects` | map | ✅ | `default` + `supported[]`; optional macro overrides.
| `data_sources` | map | ✅ | Name → {dialect, dsn_env/path, role, warehouse, database, schema}.
| `filters` | map | ✅ | `global[]` and `subject_area[]` entries with metadata.
| `subject_areas` | list | ✅ | Ordered tabs with layout + filter references.
| `kpis` | list | ✅ | KPI definitions referencing metrics/widgets.
| `widgets` | map | optional | Custom widget overrides (defaults live in code).
| `auxiliary_metrics` | list | optional | Shared datasets used by multiple widgets or tabs.
| `security` | map | optional | Role visibility + data policies.
| `refresh` | map | optional | Cache TTLs and schedule hints.
| `metadata_sources` | map | optional | Link to docs, change history, owner.

### Globals
```yaml
globals:
  timezone: America/Chicago
  default_date_range: last_30_days  # enum: last_7_days, last_30_days, qtd, ytd, last_12_months
  currency: USD                     # ISO 4217 code
  theme: cognizant_dark             # maps to theming registry
  number_format:
    decimal_places: 2
    compact_units: true
  ai_insights_enabled: true
```

### Dialects
```yaml
dialects:
  default: snowflake
  supported:
    - snowflake
    - sqlite
  macros:
    snowflake: macros/snowflake.sql
    sqlite: macros/sqlite.sql
```
Validation: default ∈ supported; macro file optional; runtime resolves to built-ins if omitted.

### Data Sources
```yaml
data_sources:
  snowflake_main:
    dialect: snowflake
    dsn_env: SNOWFLAKE_DSN
    role: ANALYST
    warehouse: KPI_WH
    database: TELECOM
    schema: ANALYTICS
  sqlite_cache:
    dialect: sqlite
    path: ./data/telecom_db.sqlite
    cache_role: fallback
    read_only: true
```
Validation: at least one Snowflake source; SQLite entries must define local path. DSN keys map to env vars; runtime refuses plaintext passwords.

### Filters
```yaml
filters:
  global:
    - id: date_range
      type: date_range
      label: Date Range
      default: last_30_days
      bindings:
        start_param: start_date
        end_param: end_date
    - id: region
      type: select
      label: Region
      data_source: snowflake_main
      sql: "SELECT DISTINCT region_name FROM dim_region ORDER BY 1"
      multi: false
  subject_area:
    network_performance:
      - id: network_element
        type: select
        label: Network Element
        data_source: snowflake_main
        sql: "SELECT DISTINCT element_name FROM dim_network_element"
        depends_on: region
```
Validation: `id` unique; `type` ∈ {date_range, select, multiselect, slider, checkbox}; optional `depends_on` must reference another filter.

### Subject Areas
```yaml
subject_areas:
  - id: network_performance
    title: "📡 Network Performance"
    icon: antenna
    order: 1
    description: "Uptime, latency, and reliability metrics"
    default_filters:
      - date_range
    layout:
      grid_columns: 12
      sections:
        - id: np_kpi_grid
          title: "Key KPIs"
          rows:
            - [ { kpi_card: kpi_network_availability }, { kpi_card: kpi_network_latency }, { kpi_card: kpi_packet_loss } ]
            - [ { kpi_card: kpi_bandwidth_util }, { kpi_card: kpi_dropped_calls }, { kpi_card: kpi_mttr } ]
        - id: np_trends
          title: "Trends"
          rows:
            - [ { chart: chart_latency_trend }, { chart: chart_uptime_trend } ]
            - [ { chart: chart_bandwidth_bar }, { chart: chart_packet_loss_area } ]
```
Validation: layout rows must fit 12-column grid; each slot references `kpi_card` or `chart` defined in KPI metadata.

### KPI & Metric Definition
```yaml
kpis:
  - id: kpi_network_availability
    title: "Network Availability"
    subject_area: network_performance
    description: "Percent uptime across monitored elements"
    owner: lee.chen@company.com
    tags: [sla, reliability]
    metrics:
      - id: metric_network_availability
        data_source: snowflake_main
        dialect: snowflake
        sql: |
          SELECT date, region, 100.0 * (1 - downtime_minutes/(24*60)) AS availability_pct
          FROM fact_network_metrics_daily
          WHERE date BETWEEN {{ date_range.start }} AND {{ date_range.end }}
            {% if filters.region %}AND region = {{ filters.region | quote }}{% endif %}
        dimensions:
          - date
          - region
        aggregations:
          card_value: last_value(availability_pct)
          delta: difference(last_value(availability_pct), period_offset(availability_pct, 'previous_period'))
        thresholds:
          good: ">= 99.9"
          warn: ">= 99.0"
          bad: "< 99.0"
        cache_ttl_seconds: 300
    widgets:
      primary:
        type: kpi_card
        value_field: card_value
        delta_field: delta
        unit: "%"
        formatting:
          decimal_places: 2
      secondary:
        - chart_id: chart_uptime_trend
          type: timeseries_line
          dataset: metric_network_availability
          encoding:
            x: date
            y: availability_pct
            color: region
```
Validation: `subject_area` must exist; metric ids unique; SQL required; dimensions list optional but recommended; thresholds follow comparison grammar (`>=`, `<=`, `<`, `>`, `between x y`).

### Auxiliary Metrics
Optional shared datasets referenced by multiple charts/widgets outside a single KPI.
```yaml
auxiliary_metrics:
  - id: metric_support_ticket_volume
    data_source: snowflake_main
    sql: |
      SELECT date, region, SUM(open_tickets) AS open_tickets
      FROM fact_support_tickets
      GROUP BY 1, 2
    cache_ttl_seconds: 600
```
Validation: `id` must not collide with KPI metric ids; widgets referencing these datasets must exist.

### Security & Refresh
```yaml
security:
  roles:
    exec:
      can_view_subject_areas: [network_performance, customer_experience]
      can_view_kpis: [kpi_revenue_growth]
    analyst:
      inherits: [exec]
      can_view_subject_areas: [revenue_monetization, usage_adoption, operations]
  row_filters:
    analyst:
      region: "{{ user.region_list }}"
refresh:
  default_ttl_seconds: 300
  overrides:
    kpi_revenue_forecast: 900
  schedule:
    cron: "*/30 * * * *"      # optional downstream scheduler hint
```

### Validation Rules
- `kpis[].metrics[].data_source` must exist in `data_sources`.
- No circular filter dependencies; runtime performs DAG check.
- Layout references (`chart_latency_trend`) must match `widgets` definitions or `kpis[].widgets.secondary[].chart_id`.
- If `metrics[].dialect` omitted, inherit from data source; overrides must be in `dialects.supported`.
- `refresh.default_ttl_seconds` ≥ 0; overrides must reference existing KPI IDs.
- Comments allowed but stripped before validation.

## Example Snippet
```yaml
schema_version: 1.0
app_version: "0.9.0"
pack_id: telecom_default
label: "Telecom KPI Dashboard"
dialects:
  default: snowflake
  supported: [snowflake, sqlite]
data_sources:
  snowflake_main:
    dialect: snowflake
    dsn_env: SNOWFLAKE_DSN
  sqlite_cache:
    dialect: sqlite
    path: ./data/telecom_db.sqlite
subject_areas:
  - id: network_performance
    title: "📡 Network Performance"
    layout:
      grid_columns: 12
      sections:
        - id: kpi_grid
          rows:
            - [ { kpi_card: kpi_network_availability }, { kpi_card: kpi_network_latency }, { kpi_card: kpi_packet_loss } ]
filters:
  global:
    - id: date_range
      type: date_range
      default: last_30_days
kpis:
  - id: kpi_network_availability
    subject_area: network_performance
    metrics:
      - id: metric_network_availability
        data_source: snowflake_main
        sql: "SELECT ..."
    widgets:
      primary:
        type: kpi_card
```

## Open Items
- Decide whether AI Insights prompt metadata belongs in core schema or a companion file.
- Clarify how benchmark management metadata integrates (separate module vs KPI flavor).
- Determine need for versioned layout overrides per resolution (desktop/tablet/mobile).
