"""Metadata-aware widget registry for the Streamlit dashboard."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Dict, Optional

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(SRC))

from improved_metric_cards import create_metric_card
from kpi_components import render_area_chart, render_bar_chart, render_line_chart

WidgetPayload = Dict[str, object]
WidgetRenderer = Callable[[WidgetPayload], None]


class WidgetRegistryError(KeyError):
    """Raised when the registry cannot resolve the requested widget."""


class WidgetRegistry:
    """Registry mapping metadata widget types to rendering callables."""

    def __init__(self) -> None:
        self._registry: Dict[str, WidgetRenderer] = {}

    def register(self, widget_type: str, renderer: WidgetRenderer) -> None:
        self._registry[widget_type] = renderer

    def resolve(self, widget_type: str) -> WidgetRenderer:
        try:
            return self._registry[widget_type]
        except KeyError as exc:  # pragma: no cover - defensive path
            raise WidgetRegistryError(widget_type) from exc

    def render(self, widget_type: str, payload: WidgetPayload) -> None:
        renderer = self.resolve(widget_type)
        renderer(payload)


_registry = WidgetRegistry()


def _ensure_dataframe(payload: WidgetPayload, empty_message: str) -> Optional[pd.DataFrame]:
    df = payload.get("dataframe")
    if not isinstance(df, pd.DataFrame) or df.empty:
        st.warning(empty_message)
        return None
    return df


def _vega_type(series: pd.Series, column: str) -> str:
    if pd.api.types.is_datetime64_any_dtype(series) or "date" in column.lower():
        return "T"
    if pd.api.types.is_numeric_dtype(series):
        return "Q"
    return "N"


def _encoding_value(encoding: WidgetPayload, key: str, default: Optional[str] = None) -> Optional[str]:
    value = encoding.get(key, default)
    return value if isinstance(value, str) else default


def _render_altair(chart: alt.Chart, title: str) -> None:
    st.altair_chart(chart.properties(title=title), use_container_width=True)


def _render_kpi_card(payload: WidgetPayload) -> None:
    value = payload.get("value")
    delta = payload.get("delta")
    label = payload.get("label", "")
    unit = payload.get("unit", "")
    help_text = payload.get("tooltip", "")
    delta_value = float(delta) if isinstance(delta, (int, float)) else 0.0
    delta_direction = "up" if delta_value > 0 else "down" if delta_value < 0 else "stable"
    create_metric_card(
        label=str(label),
        value=value if value is not None else "N/A",
        delta=delta if delta is not None else 0,
        delta_direction=delta_direction,
        unit=str(unit),
        tooltip=str(help_text),
    )


def _render_timeseries_line(payload: WidgetPayload) -> None:
    df = _ensure_dataframe(payload, "No data available for chart")
    title = payload.get("title") or "Timeseries"
    y_label = payload.get("y_label", "Value")
    if df is None:
        return
    encoding = payload.get("encoding") or {}
    x_col = _encoding_value(encoding, "x", "date")
    y_col = _encoding_value(encoding, "y") or _encoding_value(encoding, "value", "value")
    series_col = _encoding_value(encoding, "series") or _encoding_value(encoding, "color")
    if x_col in df.columns and y_col in df.columns:
        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X(f"{x_col}:{_vega_type(df[x_col], x_col)}", title=x_col.replace("_", " ").title()),
            y=alt.Y(f"{y_col}:Q", title=str(y_label)),
        )
        if series_col and series_col in df.columns:
            chart = chart.encode(color=f"{series_col}:N")
        _render_altair(chart, str(title))
        return
    render_line_chart(df, title, y_label)


def _render_bar_chart(payload: WidgetPayload) -> None:
    df = _ensure_dataframe(payload, "No data available for chart")
    title = payload.get("title", "Bar Chart")
    y_label = payload.get("y_label", "Value")
    if df is None:
        return
    encoding = payload.get("encoding") or {}
    x_col = _encoding_value(encoding, "x")
    y_col = _encoding_value(encoding, "y") or _encoding_value(encoding, "value")
    color_col = _encoding_value(encoding, "color")
    if x_col and y_col and x_col in df.columns and y_col in df.columns:
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{x_col}:{_vega_type(df[x_col], x_col)}", title=x_col.replace("_", " ").title()),
            y=alt.Y(f"{y_col}:Q", title=str(y_label)),
        )
        if color_col and color_col in df.columns:
            chart = chart.encode(color=f"{color_col}:N")
        _render_altair(chart, str(title))
        return
    render_bar_chart(df, title, y_label)


def _render_area_chart(payload: WidgetPayload) -> None:
    df = _ensure_dataframe(payload, "No data available for chart")
    title = payload.get("title", "Area Chart")
    y_label = payload.get("y_label", "Value")
    if df is None:
        return
    encoding = payload.get("encoding") or {}
    x_col = _encoding_value(encoding, "x", "date")
    y_col = _encoding_value(encoding, "y") or _encoding_value(encoding, "value", "value")
    if x_col in df.columns and y_col in df.columns:
        chart = alt.Chart(df).mark_area(opacity=0.6).encode(
            x=alt.X(f"{x_col}:{_vega_type(df[x_col], x_col)}", title=x_col.replace("_", " ").title()),
            y=alt.Y(f"{y_col}:Q", title=str(y_label)),
        )
        color_col = _encoding_value(encoding, "color")
        if color_col and color_col in df.columns:
            chart = chart.encode(color=f"{color_col}:N")
        _render_altair(chart, str(title))
        return
    render_area_chart(df, title, y_label)


def _render_placeholder(payload: WidgetPayload) -> None:
    message = payload.get("message", "Coming soon")
    st.info(message)


def _render_kpi_expandable(payload: WidgetPayload) -> None:
    """Render expandable KPI details with tooltips."""
    dataset = payload.get("dataset", "")
    df = payload.get("dataframe")
    with st.expander("📊 KPI Details", expanded=False):
        st.caption(f"Dataset: {dataset}")
        if isinstance(df, pd.DataFrame) and not df.empty:
            st.dataframe(df, width="stretch")
        else:
            st.write("No detail rows available.")


def _render_data_editor(payload: WidgetPayload) -> None:
    """Render an editable data table."""
    df = _ensure_dataframe(payload, "No data available for editing")
    if df is None:
        return

    st.data_editor(df, width="stretch")
    if payload.get("dataset") == "metric_benchmark_targets":
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("💾 Save Changes", type="primary", key="metadata_benchmark_save")
        with col2:
            st.button("📤 Export to CSV", key="metadata_benchmark_export")
        with col3:
            st.button("📥 Import from CSV", key="metadata_benchmark_import")


def _render_table(payload: WidgetPayload) -> None:
    """Render a read-only data table."""
    df = _ensure_dataframe(payload, "No data available for table")
    if df is None:
        return

    st.dataframe(df, width="stretch")


def _render_form(payload: WidgetPayload) -> None:
    """Render a form for data editing."""
    dataset = payload.get("dataset", "")
    df = payload.get("dataframe")
    if dataset == "metric_benchmark_targets" and isinstance(df, pd.DataFrame) and not df.empty:
        st.subheader("✏️ Edit Individual KPI")
        kpi_names = df["kpi_name"].tolist() if "kpi_name" in df.columns else []
        selected_kpi = st.selectbox("Select KPI to edit:", kpi_names, key="metadata_benchmark_kpi")
        if not selected_kpi:
            return
        selected_row = df[df["kpi_name"] == selected_kpi].iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "Peer Average:",
                value=float(selected_row.get("peer_avg", 0.0) or 0.0),
                step=0.1,
                format="%.2f",
                key="metadata_benchmark_peer_avg",
            )
            st.number_input(
                "Industry Average:",
                value=float(selected_row.get("industry_avg", 0.0) or 0.0),
                step=0.1,
                format="%.2f",
                key="metadata_benchmark_industry_avg",
            )
        with col2:
            st.number_input(
                "Threshold Low:",
                value=float(selected_row.get("threshold_low", 0.0) or 0.0),
                step=0.1,
                format="%.2f",
                key="metadata_benchmark_threshold_low",
            )
            st.number_input(
                "Threshold High:",
                value=float(selected_row.get("threshold_high", 100.0) or 100.0),
                step=0.1,
                format="%.2f",
                key="metadata_benchmark_threshold_high",
            )
        direction_options = ["higher_is_better", "lower_is_better", "neutral"]
        direction_value = str(selected_row.get("direction", direction_options[0]))
        direction_index = direction_options.index(direction_value) if direction_value in direction_options else 0
        st.selectbox("Direction:", direction_options, index=direction_index, key="metadata_benchmark_direction")
        st.button("💾 Update KPI", type="primary", key="metadata_benchmark_update")
        return
    with st.form(f"edit_{dataset}"):
        st.write(f"Edit form for {dataset}")
        if isinstance(df, pd.DataFrame) and not df.empty:
            st.dataframe(df, width="stretch")
        submitted = st.form_submit_button("Save Changes")
        if submitted:
            st.success("Changes captured in-session. Persistence is not wired yet.")


def _render_benchmark_table(payload: WidgetPayload) -> None:
    """Render a benchmark table with peer and industry comparisons."""
    df = _ensure_dataframe(payload, "No benchmark data available")
    if df is None:
        return

    st.subheader("📊 Benchmark Targets")
    st.dataframe(df, width="stretch")


def _render_history_table(payload: WidgetPayload) -> None:
    """Render a history table showing changes over time."""
    df = _ensure_dataframe(payload, "No history data available")
    if df is None:
        return

    st.subheader("📈 Benchmark History")
    st.dataframe(df, width="stretch")


def _render_distribution(payload: WidgetPayload) -> None:
    """Render a distribution chart."""
    df = _ensure_dataframe(payload, "No data available for distribution chart")
    title = payload.get("title", "Distribution")
    if df is None:
        return
    encoding = payload.get("encoding") or {}
    category_col = _encoding_value(encoding, "category", "category")
    value_col = _encoding_value(encoding, "value", "value")
    if category_col in df.columns and value_col in df.columns:
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{category_col}:N", title=category_col.replace("_", " ").title()),
            y=alt.Y(f"{value_col}:Q", title=value_col.replace("_", " ").title()),
        )
        _render_altair(chart, str(title))
        return
    render_bar_chart(df, title, "Value")


def _render_stacked_bar(payload: WidgetPayload) -> None:
    df = _ensure_dataframe(payload, "No data available for chart")
    title = payload.get("title", "Stacked Bar")
    if df is None:
        return
    encoding = payload.get("encoding") or {}
    x_col = _encoding_value(encoding, "x")
    y_col = _encoding_value(encoding, "y")
    color_col = _encoding_value(encoding, "color")
    if not x_col or not y_col or not color_col:
        st.dataframe(df, width="stretch")
        return
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f"{x_col}:{_vega_type(df[x_col], x_col)}", title=x_col.replace("_", " ").title()),
        y=alt.Y(f"{y_col}:Q", title=y_col.replace("_", " ").title()),
        color=f"{color_col}:N",
    )
    _render_altair(chart, str(title))


def _render_multi_series_line(payload: WidgetPayload) -> None:
    df = _ensure_dataframe(payload, "No data available for chart")
    title = payload.get("title", "Trend")
    if df is None:
        return
    encoding = payload.get("encoding") or {}
    x_col = _encoding_value(encoding, "x", "date")
    y_col = _encoding_value(encoding, "y") or _encoding_value(encoding, "value", "value")
    series_col = _encoding_value(encoding, "series")
    if not series_col or x_col not in df.columns or y_col not in df.columns or series_col not in df.columns:
        st.dataframe(df, width="stretch")
        return
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X(f"{x_col}:{_vega_type(df[x_col], x_col)}", title=x_col.replace("_", " ").title()),
        y=alt.Y(f"{y_col}:Q", title=y_col.replace("_", " ").title()),
        color=f"{series_col}:N",
    )
    _render_altair(chart, str(title))


def _render_forecast_band(payload: WidgetPayload) -> None:
    df = _ensure_dataframe(payload, "No data available for forecast")
    title = payload.get("title", "Forecast")
    if df is None:
        return
    encoding = payload.get("encoding") or {}
    x_col = _encoding_value(encoding, "x", "date")
    y_col = _encoding_value(encoding, "y") or _encoding_value(encoding, "value", "value")
    lower_col = _encoding_value(encoding, "lower")
    upper_col = _encoding_value(encoding, "upper")
    if not lower_col or not upper_col:
        st.dataframe(df, width="stretch")
        return
    band = alt.Chart(df).mark_area(opacity=0.25).encode(
        x=alt.X(f"{x_col}:{_vega_type(df[x_col], x_col)}", title=x_col.replace("_", " ").title()),
        y=alt.Y(f"{lower_col}:Q", title=y_col.replace("_", " ").title()),
        y2=f"{upper_col}:Q",
    )
    line = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X(f"{x_col}:{_vega_type(df[x_col], x_col)}"),
        y=alt.Y(f"{y_col}:Q"),
    )
    _render_altair(band + line, str(title))


def _render_heatmap(payload: WidgetPayload) -> None:
    df = _ensure_dataframe(payload, "No data available for heatmap")
    title = payload.get("title", "Heatmap")
    if df is None:
        return
    encoding = payload.get("encoding") or {}
    x_col = _encoding_value(encoding, "x")
    y_col = _encoding_value(encoding, "y")
    value_col = _encoding_value(encoding, "value")
    if not x_col or not y_col or not value_col:
        st.dataframe(df, width="stretch")
        return
    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X(f"{x_col}:N", title=x_col.replace("_", " ").title()),
        y=alt.Y(f"{y_col}:N", title=y_col.replace("_", " ").title()),
        color=alt.Color(f"{value_col}:Q", title=value_col.replace("_", " ").title()),
    )
    _render_altair(chart, str(title))


_registry.register("kpi_card", _render_kpi_card)
_registry.register("timeseries_line", _render_timeseries_line)
_registry.register("bar_chart", _render_bar_chart)
_registry.register("area_chart", _render_area_chart)
_registry.register("placeholder", _render_placeholder)
_registry.register("kpi_expandable", _render_kpi_expandable)
_registry.register("data_editor", _render_data_editor)
_registry.register("table", _render_table)
_registry.register("form", _render_form)
_registry.register("benchmark_table", _render_benchmark_table)
_registry.register("history_table", _render_history_table)
_registry.register("distribution", _render_distribution)
_registry.register("stacked_bar", _render_stacked_bar)
_registry.register("multi_series_line", _render_multi_series_line)
_registry.register("forecast_band", _render_forecast_band)
_registry.register("heatmap", _render_heatmap)


def register_widget(widget_type: str, renderer: WidgetRenderer) -> None:
    """Register or override a widget renderer."""
    _registry.register(widget_type, renderer)


def get_widget_renderer(widget_type: str) -> WidgetRenderer:
    """Retrieve a renderer for the given widget type."""
    return _registry.resolve(widget_type)


def render_widget(widget_type: str, payload: Optional[WidgetPayload] = None) -> None:
    """Render a widget using its registered renderer."""
    payload = payload or {}
    _registry.render(widget_type, payload)


__all__ = [
    "WidgetRegistryError",
    "register_widget",
    "get_widget_renderer",
    "render_widget",
]
