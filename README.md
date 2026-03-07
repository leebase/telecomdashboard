# telecomdashboard

A Streamlit-based telecom KPI dashboard with SQLite-backed demo data, theme support,
benchmarking, health checks, and optional AI-generated insights. The repo also
contains a separate multi-agent prototype under `runAgentsApp.py`.

## Primary Entry Point

```bash
streamlit run app.py
```

## Quick Start

Create or activate a virtual environment, then install the runtime dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-security.txt
```

During the current revival phase, the `requirements*.txt` files are the canonical dependency source. `pyproject.toml` is still used for packaging metadata, editable installs, and extras.

Optional: load or refresh the local SQLite demo data.

```bash
python load_csv_data.py
```

Run the main dashboard:

```bash
streamlit run app.py
```

The separate agent prototype can be launched with:

```bash
streamlit run runAgentsApp.py
```

## Development Setup

Install the package metadata and development extras if you want the helper CLI and
packaging metadata available locally:

```bash
pip install -e ".[dev]"
```

Run the maintained test suite:

```bash
pytest tests/ -v
```

Run a fast failure-focused check across the whole repo:

```bash
pytest -q -x
```

Run the built-in health report:

```bash
telecomdashboard health --pretty
telecomdashboard health --simple
```

Format and lint:

```bash
black src/ tests/ *.py
ruff check src/ tests/ *.py
```

## Updating Templates

To pull the latest AgentFlow templates into this project without overwriting your custom data, run:

```bash
init-agent --update
```

This will automatically detect the Python profile and refresh only the contract files: `AGENTS.md` and `skills/*`. Living project-memory files such as `context.md` and `WHERE_AM_I.md` are preserved.
