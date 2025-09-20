from pathlib import Path
import sqlite3

import pandas as pd
import pytest

from data.datasource import (
    DataSourceError,
    DataSourceFactory,
    SQLiteDataSource,
    SnowflakeDataSource,
)
from metadata_runtime.loader import load_metadata
from metadata_runtime.models import DataSourceConfig


def test_sqlite_datasource_executes(tmp_path):
    db_path = tmp_path / "sample.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE metrics (value INTEGER)")
    conn.executemany("INSERT INTO metrics(value) VALUES (?)", [(1,), (2,), (3,)])
    conn.commit()
    conn.close()

    config = DataSourceConfig(dialect="sqlite", path=str(db_path))
    datasource = SQLiteDataSource(config, tmp_path)
    frame = datasource.execute("SELECT value FROM metrics ORDER BY value")
    assert list(frame["value"]) == [1, 2, 3]


def test_datasource_factory_resolves_sqlite(tmp_path):
    metadata_path = Path("metadata/dashboard_telco.yaml").resolve()
    config = load_metadata(metadata_path)

    # Point sqlite cache to temporary database for the test
    db_path = tmp_path / "factory.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE dim_region (region_name TEXT)")
    conn.executemany("INSERT INTO dim_region(region_name) VALUES (?)", [("North",), ("South",)])
    conn.commit()
    conn.close()

    config.data_sources["sqlite_cache"].path = str(db_path)

    factory = DataSourceFactory(config, metadata_path)
    datasource = factory.get("sqlite_cache")
    frame = datasource.execute("SELECT region_name FROM dim_region ORDER BY region_name")
    assert frame.shape == (2, 1)
    assert frame["region_name"].tolist() == ["North", "South"]


def test_snowflake_datasource_requires_env(monkeypatch):
    config = DataSourceConfig(dialect="snowflake", dsn_env="MISSING_ENV")
    datasource = SnowflakeDataSource(config)
    with pytest.raises(DataSourceError) as excinfo:
        datasource.execute("SELECT 1")
    message = str(excinfo.value)
    assert "snowflake" in message.lower() or "missing_env" in message.lower()
    monkeypatch.delenv("MISSING_ENV", raising=False)
    assert datasource.health_check() is False
