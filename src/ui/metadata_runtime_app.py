"""Reusable renderer for the metadata-driven dashboard."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, Tuple

import streamlit as st

from data.metadata_provider import MetadataDataProvider
from metadata_runtime import MetadataConfig, MetadataLoadError, load_metadata
from metadata_runtime.models import KpiConfig, SecondaryWidgetConfig
from ui.layout_engine import render_subject_area

_DEFAULT_METADATA_PATH = Path(__file__).resolve().parents[2] / "metadata" / "dashboard_telco.yaml"
_METADATA_ENV_VAR = "DASHBOARD_METADATA_PATH"


@lru_cache(maxsize=1)
def _load_metadata_config(path: str) -> MetadataConfig:
    return load_metadata(path, force_reload=False)


def _resolve_metadata_path() -> Path:
    env_path = os.getenv(_METADATA_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser().resolve()
    return _DEFAULT_METADATA_PATH


def _build_resolver(
    provider: MetadataDataProvider,
    kpi_map: Dict[str, KpiConfig],
    chart_map: Dict[str, Tuple[KpiConfig, SecondaryWidgetConfig]],
) -> Callable[[str, str], Tuple[str, Dict[str, object]]]:
    def resolver(slot_type: str, slot_value: str):
        if slot_type == "kpi_card" and slot_value in kpi_map:
            kpi = kpi_map[slot_value]
            payload = provider.build_kpi_payload(kpi)
            return kpi.widgets.primary.type, payload

        if slot_type == "chart" and slot_value in chart_map:
            kpi, chart = chart_map[slot_value]
            payload = provider.build_chart_payload(kpi, chart)
            return chart.type, payload

        message = f"{slot_type.title()} '{slot_value}' coming soon"
        return "placeholder", {"message": message}

    return resolver


def render_metadata_dashboard(metadata_path: Path | None = None) -> None:
    """Render the metadata-driven dashboard into the active Streamlit app."""
    st.set_page_config(page_title="Metadata Dashboard", layout="wide")
    st.title("Metadata-Driven Dashboard")

    resolved_path = metadata_path or _resolve_metadata_path()
    try:
        config = _load_metadata_config(str(resolved_path))
    except FileNotFoundError:
        st.error(f"Metadata file not found at {resolved_path}")
        st.stop()
    except MetadataLoadError as exc:
        st.error("Metadata validation failed. See errors below.")
        with st.expander("Validation errors"):
            for error in exc.errors:
                loc = ".".join(str(part) for part in error.get("loc", [])) or "root"
                st.write(f"`{loc}` → {error.get('msg')}")
        st.stop()

    provider = MetadataDataProvider(config, resolved_path)

    st.sidebar.title("Metadata Pack")
    st.sidebar.markdown(
        f"**Pack ID:** `{config.pack_id}`\n\n"
        f"**Schema:** {config.schema_version}\n\n"
        f"**App Version:** {config.app_version}"
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Sources**")
    for name, source in config.data_sources.items():
        location = source.dsn_env or source.path or "(configured elsewhere)"
        st.sidebar.write(f"- `{name}` → {source.dialect} ({location})")

    kpi_map = {kpi.id: kpi for kpi in config.kpis}
    chart_map: Dict[str, Tuple[KpiConfig, SecondaryWidgetConfig]] = {}
    for kpi in config.kpis:
        for chart in kpi.widgets.secondary:
            if chart.chart_id:
                chart_map[chart.chart_id] = (kpi, chart)

    tab_labels = [area.title for area in config.subject_areas]
    tabs = st.tabs(tab_labels)

    for tab, area in zip(tabs, config.subject_areas):
        with tab:
            resolver = _build_resolver(provider, kpi_map, chart_map)
            render_subject_area(area, resolver)

    st.success("Metadata rendered via datasource-backed runtime.")


__all__ = ["render_metadata_dashboard"]
