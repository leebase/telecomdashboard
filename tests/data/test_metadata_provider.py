import sqlite3
from pathlib import Path

import pandas as pd

from data.metadata_provider import MetadataDataProvider
from metadata_runtime.loader import load_metadata


def _seed_network_latency_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE fact_network_metrics (
                network_element_id INTEGER,
                date_id TEXT,
                region_id INTEGER,
                uptime_seconds REAL,
                downtime_seconds REAL,
                latency_ms REAL,
                packet_loss_percent REAL,
                bandwidth_utilization_percent REAL,
                mttr_hours REAL,
                dropped_call_rate REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE dim_region (
                region_id INTEGER PRIMARY KEY,
                region_name TEXT
            )
            """
        )
        conn.executemany(
            "INSERT INTO dim_region(region_id, region_name) VALUES (?, ?)",
            [(1, "North"), (2, "South")],
        )
        rows = [
            (101, "2023-07-01", 1, 1000, 10, 42.0, 0.2, 65.0, 2.5, 0.3),
            (102, "2023-07-02", 1, 1100, 5, 45.0, 0.15, 64.0, 2.4, 0.25),
            (103, "2023-07-02", 2, 1050, 12, 55.0, 0.3, 70.0, 2.7, 0.35),
        ]
        conn.executemany(
            "INSERT INTO fact_network_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def test_metadata_provider_returns_kpi_payload(tmp_path):
    db_path = tmp_path / "network.sqlite"
    _seed_network_latency_db(db_path)

    metadata_path = Path("metadata/dashboard_telco.yaml").resolve()
    config = load_metadata(metadata_path)
    config.data_sources["sqlite_cache"].path = str(db_path)

    provider = MetadataDataProvider(config, metadata_path)

    kpi = next(k for k in config.kpis if k.id == "kpi_network_latency")
    payload = provider.build_kpi_payload(kpi)

    assert payload["label"] == kpi.title
    assert isinstance(payload["value"], float)

    chart = next(c for c in kpi.widgets.secondary if c.chart_id == "chart_latency_trend")
    chart_payload = provider.build_chart_payload(kpi, chart)
    dataframe = chart_payload["dataframe"]

    assert not dataframe.empty
    assert set(["date", "value"]).issubset(dataframe.columns)
