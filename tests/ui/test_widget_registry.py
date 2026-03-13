from __future__ import annotations

import pytest

from ui.metadata_widgets import (
    WidgetRegistryError,
    get_widget_renderer,
    register_widget,
    render_widget,
)


def test_get_default_renderer():
    renderer = get_widget_renderer("kpi_card")
    assert callable(renderer)


def test_area_chart_renderer_available():
    renderer = get_widget_renderer("area_chart")
    assert callable(renderer)


def test_telco_pack_renderers_available():
    for widget_type in ["stacked_bar", "multi_series_line", "forecast_band", "heatmap"]:
        renderer = get_widget_renderer(widget_type)
        assert callable(renderer)


def test_render_unknown_widget_raises():
    with pytest.raises(WidgetRegistryError):
        render_widget("non_existent", {})


def test_register_custom_widget(monkeypatch):
    calls = []

    def _custom_renderer(payload):
        calls.append(payload)

    register_widget("custom", _custom_renderer)
    render_widget("custom", {"foo": "bar"})
    assert calls == [{"foo": "bar"}]
