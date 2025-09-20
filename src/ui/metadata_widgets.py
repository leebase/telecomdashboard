"""Metadata-aware widget registry for the Streamlit dashboard."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Dict, Optional

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(SRC))

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


def _render_kpi_card(payload: WidgetPayload) -> None:
    value = payload.get("value")
    delta = payload.get("delta")
    label = payload.get("label", "")
    unit = payload.get("unit", "")
    help_text = payload.get("tooltip", "")
    st.metric(label=label, value=value, delta=delta, help=help_text)


def _render_timeseries_line(payload: WidgetPayload) -> None:
    df = payload.get("dataframe")
    title = payload.get("title") or "Timeseries"
    y_label = payload.get("y_label", "Value")
    if not isinstance(df, pd.DataFrame):
        st.warning("No data available for chart")
        return
    render_line_chart(df, title, y_label)


def _render_bar_chart(payload: WidgetPayload) -> None:
    df = payload.get("dataframe")
    title = payload.get("title", "Bar Chart")
    y_label = payload.get("y_label", "Value")
    if not isinstance(df, pd.DataFrame):
        st.warning("No data available for chart")
        return
    render_bar_chart(df, title, y_label)


def _render_area_chart(payload: WidgetPayload) -> None:
    df = payload.get("dataframe")
    title = payload.get("title", "Area Chart")
    y_label = payload.get("y_label", "Value")
    if not isinstance(df, pd.DataFrame):
        st.warning("No data available for chart")
        return
    render_area_chart(df, title, y_label)


def _render_placeholder(payload: WidgetPayload) -> None:
    message = payload.get("message", "Coming soon")
    st.info(message)


_registry.register("kpi_card", _render_kpi_card)
_registry.register("timeseries_line", _render_timeseries_line)
_registry.register("bar_chart", _render_bar_chart)
_registry.register("area_chart", _render_area_chart)
_registry.register("placeholder", _render_placeholder)


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
