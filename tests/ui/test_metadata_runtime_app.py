from pathlib import Path

from metadata_runtime.loader import load_metadata
from ui.metadata_runtime_app import _build_resolver


class DummyProvider:
    def build_kpi_payload_for_filters(self, kpi, runtime_filters=None):
        return {"kind": "kpi", "id": kpi.id}

    def build_chart_payload(self, kpi, chart, runtime_filters=None):
        return {"kind": "chart", "id": chart.chart_id, "kpi": kpi.id}

    def build_widget_payload(self, widget, title=None, runtime_filters=None):
        return {"kind": "widget", "dataset": widget.dataset, "type": widget.type, "title": title}


def _load_maps():
    config = load_metadata(Path("metadata/dashboard_telco.yaml").resolve())
    kpi_map = {kpi.id: kpi for kpi in config.kpis}
    chart_map = {}
    for kpi in config.kpis:
        for chart in kpi.widgets.secondary:
            if chart.chart_id:
                chart_map[chart.chart_id] = (kpi, chart)
    widget_map = dict(config.widgets.__root__)
    return kpi_map, chart_map, widget_map


def test_build_resolver_prefers_kpi_chart_definitions():
    provider = DummyProvider()
    kpi_map, chart_map, widget_map = _load_maps()

    resolver = _build_resolver(provider, kpi_map, chart_map, widget_map, {})
    widget_type, payload = resolver("chart", "chart_latency_trend")

    assert widget_type == "timeseries_line"
    assert payload == {"kind": "chart", "id": "chart_latency_trend", "kpi": "kpi_network_latency"}


def test_build_resolver_handles_metadata_widget_slots():
    provider = DummyProvider()
    kpi_map, chart_map, widget_map = _load_maps()

    resolver = _build_resolver(provider, kpi_map, chart_map, widget_map, {})
    widget_type, payload = resolver("widget", "widget_benchmark_table")

    assert widget_type == "data_editor"
    assert payload["kind"] == "widget"
    assert payload["dataset"] == "metric_benchmark_targets"


def test_build_resolver_handles_metadata_chart_overrides():
    provider = DummyProvider()
    kpi_map, chart_map, widget_map = _load_maps()

    resolver = _build_resolver(provider, kpi_map, chart_map, widget_map, {})
    widget_type, payload = resolver("chart", "chart_revenue_trend")

    assert widget_type == "timeseries_line"
    assert payload["kind"] == "widget"
    assert payload["dataset"] == "metric_revenue_trend"
