# telecomdashboard Architecture

> Current architecture summary for the revived codebase.

---

## Primary Runtime

The main application is the Streamlit dashboard launched with:

```bash
streamlit run app.py
```

`app.py` coordinates the UI, pulls KPI data, applies theme styling, exposes AI insight actions, and wires in benchmark and operational helpers.

---

## Major Components

### UI and Presentation

- `app.py`: top-level Streamlit app and tab rendering
- `kpi_components.py`: charts, metric cards, and KPI explainers
- `improved_metric_cards.py`: richer KPI card rendering and metric retrieval helpers
- `theme_manager.py`, `theme_switcher.py`, `cognizant_theme.py`, `verizon_theme.py`: theme selection and theme assets
- `benchmark_manager.py`: benchmark-related UI and logic

### Data and Storage

- `database_connection.py`: SQLite access plus connection and query helpers
- `data/`: local SQLite database, CSV inputs, schema SQL, and data catalog
- `load_csv_data.py`, `load_data.py`, `setup_database.py`: data bootstrap scripts

### AI and Analysis

- `ai_insights_data_bundler.py`: packages KPI context for analysis
- `ai_insights_ui.py`: renders the AI insights panel
- `llm_service.py`: provider integration, retries, and formatting
- `ai_insights_prompts.yaml`: prompt templates and structure

### Operations and Safety

- `config_manager.py`, `config_loader.py`, `config_validator.py`: config loading and validation
- `security_manager.py`: output sanitization, security controls, and headers
- `health_check.py`: health endpoints and feature flag exposure
- `logging_config.py`: structured and operational logging
- `performance_utils.py`: performance helpers and monitoring support

### Tests

- `tests/security/`
- `tests/ai/`
- `tests/performance/`
- `tests/integration/`
- `tests/config/`
- `tests/unit/`

---

## Secondary Prototype

A separate Streamlit app exists in:

```bash
streamlit run runAgentsApp.py
```

Supporting code lives in:

- `agents/`
- `models/play_models.py`
- `test_phase1.py`
- `test_phase2.py`
- `test_phase2_integration.py`
- `test_phase3_ui.py`

This prototype appears to be a playbook prioritization and portfolio orchestration experiment. It is not currently treated as the default product surface.

---

## Known Architectural Drift

- `README.md` and `pyproject.toml` still describe a generic scaffold instead of the real dashboard
- `src/telecomdashboard/main.py` is a hello-world style CLI and not aligned with the Streamlit app
- `Makefile` references `requirements-dev.txt`, but that file is not present
- Dependency declarations had drifted from the code; runtime needs `requests`, and the current codebase requires `pydantic<2`

## Dependency Source Policy

- `requirements.txt`, `requirements-security.txt`, and `requirements-dev.txt` are the canonical install sources for the revival phase
- `pyproject.toml` remains useful for packaging metadata, editable installs, and optional extras, but it is not yet the primary environment definition
- This is intentional because the repo still operates as a top-level application with important modules outside the `src/` package boundary

---

## Working Assumption For Future Sessions

Unless the task explicitly targets the prototype, optimize for the main dashboard in `app.py` and treat the rest of the repo as supporting or legacy context.
