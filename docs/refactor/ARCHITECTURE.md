# Metadata Runtime Architecture

## Summary
Convert the telecom-centric Streamlit dashboard into a metadata-driven runtime that can render any industry’s KPIs by swapping YAML domain packs. The new runtime keeps the existing UI parity while introducing validated metadata, templated SQL, widget registry, and portable data-source abstractions (Snowflake primary, SQLite cache/local dev).

## Goals & Non-Goals
- **Goals:** metadata-first rendering; cross-industry packs; no-regression telco parity; Snowflake/SQLite dialect support; auditable configuration; observability hooks.
- **Non-Goals:** implementing runtime code in this pass; POML-based prompt flows; non-Python frontends.

## Runtime Flow
```
┌────────────┐   load+merge   ┌───────────────┐   validated   ┌──────────────┐
│ YAML files │──────────────▶│ Schema Loader │──────────────▶│ Domain Model │
└────────────┘               └──────┬────────┘               └──────┬───────┘
                                     │ resolve datasource + layout   │
                                     ▼                               ▼
                               ┌─────────────┐   compiled SQL   ┌──────────────┐
                               │ Dialect &   │─────────────────▶│ Data Engine  │
                               │ Macro Bank  │                  │ (async pool) │
                               └────┬────────┘                  └────┬─────────┘
                                    │ transforms + caching           │ widgets
                                    ▼                                ▼
                               ┌─────────────┐   widget props   ┌──────────────┐
                               │ Metric/KPI  │─────────────────▶│ Widget &     │
                               │ Orchestrator│                  │ Layout Runner│
                               └─────────────┘                  └──────────────┘
```

## Component Model
- **DataSource:** connection factory keyed by `data_sources.*` (Snowflake DSN env, SQLite path). Supports credential injection, connection pooling, retry/circuit breaker, query logging.
- **Dialect:** registry defining macros (date trunc, qualifiy emulation, limit syntax), default per pack, optional overrides per KPI. Template engine = Jinja2 with macro library.
- **SubjectArea:** tab-level container (id, title, icon, order, layout grid, default filters, navigation hints). Supports nested sections and responsive breakpoints.
- **KPI:** owns semantic description, owner, tags, metrics, widget binding, thresholds, SLOs, refresh cadence, security roles. Delegates to **Metric** definitions for query + transforms.
- **Metric:** encapsulates SQL template, dimensions, aggregates, derived fields, optional python transform entrypoint. Supports multi-metric KPIs (e.g., card + timeseries from same query).
- **Dimension & Filter:** defines allowed slicers (global vs subject-area). Filter metadata describes widget type, source query, default, dependency graph, and security scopes.
- **Widget:** registry mapping metadata `widget.type` → Python component (metric card, timeseries_line, bar, area, distribution, table, bullet, funnel, benchmark_table, ai_button). Widgets declare required fields/encodings.
- **Chart & Layout:** chart spec describes encoding (x/y/measure, grouping, annotations). Layout interpreter consumes 12-column grid with sections → rows → slots; supports responsive breakpoints and print-mode expansion.
- **Threshold/Formatting:** rule engine evaluating numeric/string thresholds (>=, <=, between) to determine card coloring, delta arrows, badges. Supports templated tooltips.
- **Navigation:** metadata for tab order, sidebar links, breadcrumbs, deep links, and optional hidden packs.
- **Access Control:** role → subject_area/KPI/filter visibility, enforced pre-render (metadata prune) and during query compilation (row-level filters/macros).
- **Caching & Refresh:** TTL per KPI + shared cache contexts (in-memory, SQLite table, Snowflake result cache). Supports scheduled refresh metadata and invalidation triggers (filter combos).

## Cross-Industry Portability
- **Domain Packs:** `metadata/packs/<industry>.yaml` encapsulate subject areas, KPIs, filters, naming conventions. Telco pack auto-generated from legacy config; future retail/healthcare packs reuse same schema.
- **Semantic Mapping:** shared vocabulary (availability, churn, ARPU) mapped to canonical concept IDs; pack metadata can alias concept → label for industry phrasing.
- **Theming:** pack can reference theme token set (e.g., telecom_dark) while reusing base components. Theme metadata stored separately but referenced by pack.

## SQL Templating & Dialects
- Use Jinja2 templates with macro library per dialect (`macros/snowflake.sql`, `macros/sqlite.sql`).
- Support filters via named parameters (`{{ filters.date_range.start }}`) with macro helpers for date trunc, percentile, QUALIFY emulation.
- Diff-aware compilation: run template through dialect translator, log compiled SQL for observability, gate by allow-listed macros.
- Provide unit tests comparing rendered SQL for Snowflake vs SQLite using golden files.

## Execution Lifecycle
1. Load base metadata, merge with environment overrides, validate via Pydantic models.
2. Build domain graph (datasources, filters, KPIs) with dependency resolution and access control pruning.
3. For each tab render, materialize filter state → compile metrics → execute via async engine with circuit breaker + retry.
4. Apply caching rules; hydration step converts DataFrames into widget input payloads with formatting (units, decimals, thresholds).
5. Widget runner instantiates components from registry, renders layout, triggers optional AI insight contexts.

## Testing & Observability
- **Validation:** JSON Schema + Pydantic to catch structural errors; CLI `metadata validate` command with rich diffs.
- **Data Contracts:** sample datasets validated against expected columns/dtypes; golden CSV assertions for KPI outputs.
- **Visual Regression:** Storybook-style headless render (Streamlit component test harness) capturing DOM snapshots/screenshots per layout section.
- **Logging/Tracing:** structured logs (metadata id, datasource, latency), OpenTelemetry spans around compile/run, metrics for cache hit rate and error budgets.
- **SLO Tracking:** metadata includes refresh cadence + SLO; runtime records actual latency and data age for operator dashboards.

## Security & Access
- Sensitive secrets remain in environment/secret manager; metadata stores DSN keys only.
- Role-based trimming of subject areas/KPIs before rendering; parameter whitelists prevent injection.
- Audit log for metadata changes (git + runtime change feed) with hash verification.

## Open Items
- Decide on multi-file vs single-file metadata pack inclusion strategy.
- Confirm need for AI insight metadata (prompt templates, context features) in this schema or future POML doc.
- Evaluate requirement for offline/mobile layouts (influences layout interpreter scope).
