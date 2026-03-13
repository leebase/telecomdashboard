"""Reusable renderer for the metadata-driven dashboard."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Tuple

import streamlit as st

from data.metadata_provider import MetadataDataProvider
from metadata_runtime import MetadataConfig, MetadataLoadError, load_metadata
from metadata_runtime.models import KpiConfig, SecondaryWidgetConfig, WidgetRegistryOverride
from theme_manager import get_current_theme_css, get_current_theme_header, get_current_theme_page_header
from theme_switcher import create_theme_switcher
from ui.layout_engine import render_subject_area

_DEFAULT_METADATA_PATH = Path(__file__).resolve().parents[2] / "metadata" / "dashboard_telco.yaml"
_METADATA_ENV_VAR = "DASHBOARD_METADATA_PATH"
_PAGE_HEADER_TITLE = "Network Performance & Reliability"
_PAGE_HEADER_DESCRIPTION = (
    "Select a time period and explore KPIs across Network Performance, Customer Experience, "
    "Revenue & Monetization, Usage & Adoption, and Operational Efficiency."
)
_AREA_TITLES = {
    "network_performance": "📡 Network Performance & Reliability",
    "customer_experience": "😊 Customer Experience & Retention",
    "revenue_monetization": "💰 Revenue & Monetization",
    "usage_adoption": "📶 Usage & Service Adoption",
    "operational_efficiency": "🛠️ Operational Efficiency",
    "benchmark_management": "🎯 Benchmark Management",
}
_TIME_PERIOD_LABELS = {
    "last_7_days": "Last 7 Days",
    "last_30_days": "Last 30 Days",
    "qtd": "QTD",
    "ytd": "YTD",
    "last_12_months": "Last 12 Months",
}
_TIME_PERIOD_TO_ALIAS = {label: alias for alias, label in _TIME_PERIOD_LABELS.items()}
_PRINT_CSS = """
<style>
@media print {
    [data-testid="stTabs"] > div:first-child {
        display: none !important;
    }
    [data-testid="stTabs"] > div:not(:first-child) {
        display: block !important;
        page-break-inside: avoid;
        margin-bottom: 30px;
    }
    [data-testid="stTabs"] > div:not(:first-child):not(:last-child) {
        page-break-after: always;
    }
    [data-testid="stSidebar"] {
        display: none !important;
    }
    .main .block-container {
        padding: 0 !important;
        max-width: none !important;
    }
}
</style>
"""


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
    widget_map: Dict[str, WidgetRegistryOverride],
    runtime_filters: Mapping[str, Any],
) -> Callable[[str, str], Tuple[str, Dict[str, object]]]:
    def resolver(slot_type: str, slot_value: str):
        if slot_type == "kpi_card" and slot_value in kpi_map:
            kpi = kpi_map[slot_value]
            payload = provider.build_kpi_payload_for_filters(kpi, runtime_filters)
            return kpi.widgets.primary.type, payload

        if slot_type == "chart" and slot_value in chart_map:
            kpi, chart = chart_map[slot_value]
            payload = provider.build_chart_payload(kpi, chart, runtime_filters)
            return chart.type, payload

        if slot_value in widget_map:
            widget = widget_map[slot_value]
            payload = provider.build_widget_payload(widget, runtime_filters=runtime_filters)
            return widget.type, payload

        message = f"{slot_type.title()} '{slot_value}' coming soon"
        return "placeholder", {"message": message}

    return resolver


def _render_metadata_shell() -> None:
    st.markdown(get_current_theme_css(), unsafe_allow_html=True)
    st.markdown(_PRINT_CSS, unsafe_allow_html=True)
    st.markdown(get_current_theme_header(), unsafe_allow_html=True)

    create_theme_switcher()
    if st.sidebar.button("🖨️ Print All Tabs"):
        st.sidebar.info("🚧 Print functionality coming soon!")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Quick Print Links:**")
    if st.sidebar.button("📄 Open Print Mode"):
        st.sidebar.info("🚧 Print functionality coming soon!")

    st.markdown(
        get_current_theme_page_header(_PAGE_HEADER_TITLE, _PAGE_HEADER_DESCRIPTION),
        unsafe_allow_html=True,
    )


def _render_subject_area_chrome(area_id: str) -> Dict[str, Any]:
    area_title = _AREA_TITLES.get(area_id, area_id.replace("_", " ").title())

    if area_id == "benchmark_management":
        st.header(area_title, divider=False)
        st.caption("Manage peer and industry benchmark targets for AI Insights.")
        return {}

    header_col, action_col = st.columns([5, 1])
    with header_col:
        st.header(area_title, divider=False)
    with action_col:
        st.markdown(
            '<div style="height: 3.3rem; display: flex; align-items: flex-end; justify-content: flex-end;">',
            unsafe_allow_html=True,
        )
        if st.button("🤖 AI Insights", key=f"metadata_ai_{area_id}", type="secondary", width="stretch"):
            st.info("AI Insights are not wired into metadata mode yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    selected_label = st.selectbox(
        "Select Time Period",
        list(_TIME_PERIOD_TO_ALIAS.keys()),
        index=list(_TIME_PERIOD_TO_ALIAS.values()).index("last_30_days"),
        key=f"time_period_selector_{area_id}",
    )
    return {"date_range": _TIME_PERIOD_TO_ALIAS[selected_label]}


def render_metadata_dashboard(metadata_path: Path | None = None) -> None:
    """Render the metadata-driven dashboard into the active Streamlit app."""
    st.set_page_config(page_title="Metadata Dashboard", layout="wide")

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
    _render_metadata_shell()

    kpi_map = {kpi.id: kpi for kpi in config.kpis}
    chart_map: Dict[str, Tuple[KpiConfig, SecondaryWidgetConfig]] = {}
    for kpi in config.kpis:
        for chart in kpi.widgets.secondary:
            if chart.chart_id:
                chart_map[chart.chart_id] = (kpi, chart)
    widget_map = dict(config.widgets.__root__) if config.widgets else {}

    tab_labels = [area.title for area in config.subject_areas]
    tabs = st.tabs(tab_labels)

    for tab, area in zip(tabs, config.subject_areas):
        with tab:
            runtime_filters = _render_subject_area_chrome(area.id)
            resolver = _build_resolver(provider, kpi_map, chart_map, widget_map, runtime_filters)
            render_subject_area(area, resolver)


__all__ = ["render_metadata_dashboard"]
