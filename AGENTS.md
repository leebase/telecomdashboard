# Repository Guidelines

## Project Structure & Module Organization
Main Streamlit app in `app.py`; agent orchestrations in `runAgentsApp.py`. Domain logic stays in `src/` (`core`, `services`, `ui`, `utils`), with reusable agent actions in `agents/`. The star-schema warehouse lives under `data/` (`telecom_db.sqlite`, 19 CSVs, seven dimensions, five fact tables). Review `docs/appArchitecture.md` and `docs/appRequirements.md` for architecture, KPI, and theming context before large changes. Config artifacts live in `config/`; brand themes live in `styles/`.

## Architecture & Platform Notes
Streamlit 1.28+, Altair, pandas, and NumPy power the UI. `database_connection.py` layers a 5-minute TTL cache over SQLite reads and is ready for enterprise adapters. `llm_service.py` protects OpenRouter calls with a circuit breaker (five failures trigger a 60 s cooldown). Time selectors (30D/QTD/YTD/12M) feed the warehouse business views. Theme registration runs through `theme_manager.py`; new themes need CSS, a Python module, logo assets, and registry wiring.

## Build, Test, and Development Commands
Activate the venv (`source venv/bin/activate`). `make install` installs dependencies, `make run` launches the dashboard, and `make run-dev` enables hot reload with `DEBUG=1`. Database prep runs via `make db-setup` + `make db-load`; regenerate data with `python load_csv_data.py`. `make docs` builds Sphinx docs, and `make security-check` runs Bandit and Safety.

## Coding Style & Naming Conventions
Use four-space indentation, snake_case names, and Black/isort order enforced by `make lint` or `make lint-fix`. Keep ≤100 character lines per flake8. Document public functions with succinct docstrings clarifying inputs, outputs, and business impact. Store prompt YAML, theme CSS, and fixtures beside the feature that owns them.

## Testing Guidelines
Pytest is configured in `pytest.ini` with strict markers and an 80% coverage floor. Run `pytest tests/ -v` for the suite or scope to directories (`tests/security`, `tests/performance`, etc.). Mirror the `tests/` layout when adding cases and prefer `test_<feature>.py` naming.

## Commit & Pull Request Guidelines
Write imperative, scoped commits (e.g., `Add circuit breaker telemetry`). PRs should restate intent, list verification steps (`pytest`, `make lint`, relevant `make test-*`), link issues/specs, and attach UI or agent screenshots or demos when visuals change. Highlight configuration updates (new env vars, YAML keys) in the description.

## Security & Configuration Tips
Never commit `config.secrets.yaml`; rely on `setup_secure_environment.py` or environment variables (`LLM_API_KEY`, `SECURE_MODE`). Lock down generated SQLite assets with `chmod 600`. When integrating new data sources or APIs, extend `secure_config_manager.py`, update `SECURITY.md`, and double-check caching or prompt changes against the security checklist. Route sensitive logging through `logging_config.py` and scrub PII before writing to `logs/`.
