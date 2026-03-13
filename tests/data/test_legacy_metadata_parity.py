from __future__ import annotations

from pathlib import Path

from database_connection import TelecomDatabase
from data.metadata_provider import MetadataDataProvider
from metadata_runtime.loader import load_metadata


NETWORK_KPI_MAP = {
    "kpi_network_availability": "avg_availability",
    "kpi_network_latency": "avg_latency",
    "kpi_packet_loss": "avg_packet_loss",
    "kpi_bandwidth_utilization": "avg_bandwidth_util",
    "kpi_dropped_call_rate": "avg_dropped_call_rate",
    "kpi_mttr": "avg_mttr",
}


def test_network_kpi_values_match_legacy_rollups():
    metadata_path = Path("metadata/dashboard_telco.yaml").resolve()
    config = load_metadata(metadata_path)
    config.data_sources["sqlite_cache"].path = str(Path("data/telecom_db.sqlite").resolve())
    provider = MetadataDataProvider(config, metadata_path)
    legacy_db = TelecomDatabase("data/telecom_db.sqlite")

    legacy_metrics = legacy_db.get_network_metrics(days=30)
    runtime_filters = {
        "date_range": {"start": "2023-08-01", "end": "2023-08-01"},
        "region": None,
    }

    for kpi_id, legacy_key in NETWORK_KPI_MAP.items():
        kpi = next(item for item in config.kpis if item.id == kpi_id)
        payload = provider.build_kpi_payload_for_filters(kpi, runtime_filters)
        assert payload["value"] is not None
        assert abs(float(payload["value"]) - float(legacy_metrics[legacy_key])) < 0.11


def test_network_chart_payloads_stay_populated_for_legacy_proof_date():
    metadata_path = Path("metadata/dashboard_telco.yaml").resolve()
    config = load_metadata(metadata_path)
    config.data_sources["sqlite_cache"].path = str(Path("data/telecom_db.sqlite").resolve())
    provider = MetadataDataProvider(config, metadata_path)
    runtime_filters = {
        "date_range": {"start": "2023-08-01", "end": "2023-08-01"},
        "region": None,
    }

    chart_ids = [
        "chart_latency_trend",
        "chart_uptime_trend",
        "chart_bandwidth_region",
        "chart_packet_loss_trend",
    ]

    for chart_id in chart_ids:
        kpi = next(item for item in config.kpis if any(chart.chart_id == chart_id for chart in item.widgets.secondary))
        chart = next(chart for chart in kpi.widgets.secondary if chart.chart_id == chart_id)
        payload = provider.build_chart_payload(kpi, chart, runtime_filters)

        assert not payload["dataframe"].empty
