"""Entry point for the metadata-only Streamlit app."""
from __future__ import annotations

from pathlib import Path

from ui.metadata_runtime_app import render_metadata_dashboard


def main() -> None:
    render_metadata_dashboard()


if __name__ == "__main__":  # pragma: no cover
    main()
