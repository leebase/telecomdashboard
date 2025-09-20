# Inventory – Telecom Dashboard (Pre-Refactor)

## Overview
- **Entry point:** `app.py` renders six Streamlit tabs (Network, Customer, Revenue, Usage, Operations, Benchmark Manager) and wires them to helper modules.
- **UI helpers:** `improved_metric_cards.py` supplies KPI card grid, time selectors, and data fetch hooks; `kpi_components.py` renders Altair charts (line, bar, area, distribution) and info expanders.
- **AI & theming:** `ai_insights_*` files handle LLM prompts, while `theme_manager.py` and `theme_switcher.py` control Cognizant/Verizon themes.

## Subject Areas & KPIs
- **Network Performance:** `render_network_performance` + `TelecomDatabase.get_network_metrics`. KPIs: Availability, Latency, Bandwidth Utilization, Dropped Call Rate, Packet Loss Rate, MTTR. Charts: line (latency, availability), bar (bandwidth by region), area (packet loss). Tooltip definitions via `render_kpi_expander`.
- **Customer Experience:** `render_customer_experience`, `get_customer_metrics`. KPIs: Customer Satisfaction, NPS, Churn Rate, Average Handling Time, First Contact Resolution, Customer Lifetime Value. Charts: line (NPS trend), bar (support tickets), distribution (sentiment).
- **Revenue & Monetization:** `render_revenue_monetization`, `get_revenue_metrics`. KPIs: ARPU, EBITDA Margin, Customer Acquisition Cost, Customer Lifetime Value, Revenue Growth, Profit Margin. Charts: area (revenue trend), bar (product revenue mix), line (forecast), table for metrics.
- **Usage & Adoption:** `render_usage_adoption`, `get_usage_metrics`. KPIs: Data Usage per Subscriber, 5G Adoption Rate, Feature Adoption, Service Penetration, App Usage, Premium Service Adoption. Charts: stacked bar (plan usage), line (feature adoption), distribution (usage tiers).
- **Operational Efficiency:** `render_operational_efficiency`, `get_operations_metrics`. KPIs: Service Response Time, Regulatory Compliance, Capex-to-Revenue, Network Efficiency Score, Ticket Resolution, System Uptime. Charts: heatmap/table (incident backlog), line (uptime), bar (response by region).
- **Benchmark Management:** `benchmark_manager.py` exposes editable dataframe tied to `db.get_benchmark_targets()` and change history.

## Filters & Navigation
- Time-period selector per tab (`create_time_period_selector`) with options Last 30 Days / QTD / YTD / Last 12 Months; maps to `TelecomDatabase` query variants that scale metrics.
- Print mode (currently disabled) would render all tabs sequentially. No global slicers beyond time-period.

## Data Access & Security
- **Database layer:** `TelecomDatabase` in `database_connection.py` (SQLite path `data/telecom_db.sqlite`) with TTL cache decorator, secure query executor, and simulated time-period adjustments.
- **Data generation:** `generate_*_data.py` synthesize data for charts when DB is thin; charts expect DataFrames shaped with `date`, `value`, `region`, etc.
- **Benchmarks:** CRUD via `db.update_benchmark_target`, history, CSV import/export in `setup_benchmark_tables.py`.
- **Security:** `security_manager.py` enforces sanitized queries; logging wired via `logging_config.py`.

## Open Items
- Confirm actual Snowflake queries (current SQL hardcodes `date_id = '2023-08-01'`); need production sources.
- Document exact chart schemas (columns, dtypes) for metadata-driven renderer.
- Determine shared filters beyond time (region, product) that roadmap expects.
- Clarify AI Insights dependencies on KPI metadata to avoid double maintenance.
