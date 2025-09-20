"""Datasource abstraction for metadata runtime queries."""
from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from metadata_runtime.models import DataSourceConfig, MetadataConfig

logger = logging.getLogger(__name__)


class DataSourceError(RuntimeError):
    """Raised when datasource operations fail."""


class BaseDataSource:
    """Interface for datasource implementations."""

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        raise NotImplementedError

    def health_check(self) -> bool:
        raise NotImplementedError


class SQLiteDataSource(BaseDataSource):
    def __init__(self, config: DataSourceConfig, base_path: Path) -> None:
        self._read_only = config.read_only
        raw_path = config.path or ""
        path = Path(raw_path)
        if not path.is_absolute():
            path = (base_path / path).resolve()
        self._path = path

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        params = params or {}
        try:
            conn = sqlite3.connect(str(self._path))
        except sqlite3.Error as exc:  # pragma: no cover - propagation
            raise DataSourceError(f"Failed to connect to SQLite database: {exc}") from exc
        try:
            frame = pd.read_sql_query(sql, conn, params=params)
            return frame
        except sqlite3.Error as exc:
            raise DataSourceError(f"SQLite execution error: {exc}") from exc
        finally:
            conn.close()

    def health_check(self) -> bool:
        try:
            conn = sqlite3.connect(str(self._path))
            conn.execute("SELECT 1")
            conn.close()
            return True
        except sqlite3.Error:
            return False


class SnowflakeDataSource(BaseDataSource):
    def __init__(self, config: DataSourceConfig) -> None:
        if not config.dsn_env:
            raise DataSourceError("Snowflake data source requires 'dsn_env'")
        self._dsn_env = config.dsn_env
        self._role = config.role
        self._warehouse = config.warehouse
        self._database = config.database
        self._schema = config.schema

    def _connect_params(self) -> Dict[str, Any]:
        dsn = os.getenv(self._dsn_env or "")
        if not dsn:
            raise DataSourceError(f"Environment variable '{self._dsn_env}' not set for Snowflake datasource")
        params: Dict[str, Any] = {}
        for part in dsn.split(";"):
            if not part:
                continue
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            params[key.strip()] = value.strip()
        if "user" not in params or "password" not in params:
            raise DataSourceError("Snowflake DSN must include 'user' and 'password'")
        if self._role:
            params.setdefault("role", self._role)
        if self._warehouse:
            params.setdefault("warehouse", self._warehouse)
        if self._database:
            params.setdefault("database", self._database)
        if self._schema:
            params.setdefault("schema", self._schema)
        return params

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        try:
            import snowflake.connector  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment specific
            raise DataSourceError("snowflake-connector-python is not installed") from exc

        conn_params = self._connect_params()
        try:
            with snowflake.connector.connect(**conn_params) as connection:
                frame = pd.read_sql(sql, connection, params=params)
            return frame
        except Exception as exc:  # pragma: no cover - network dependent
            raise DataSourceError(f"Snowflake execution failed: {exc}") from exc

    def health_check(self) -> bool:
        try:
            import snowflake.connector  # type: ignore
        except ImportError:
            return False
        try:
            conn_params = self._connect_params()
            with snowflake.connector.connect(**conn_params) as connection:
                connection.cursor().execute("SELECT 1")
            return True
        except Exception:
            return False


class DataSourceFactory:
    """Factory that instantiates datasources from metadata configuration."""

    def __init__(self, config: MetadataConfig, metadata_path: Path) -> None:
        self._config = config
        self._metadata_path = metadata_path.resolve()
        self._cache: Dict[str, BaseDataSource] = {}

    def get(self, data_source_id: str) -> BaseDataSource:
        if data_source_id in self._cache:
            return self._cache[data_source_id]

        ds_config = self._config.data_sources.get(data_source_id)
        if not ds_config:
            raise DataSourceError(f"Data source '{data_source_id}' not defined")

        base_path = self._metadata_path.parent
        if ds_config.dialect == "sqlite":
            datasource: BaseDataSource = SQLiteDataSource(ds_config, base_path)
        elif ds_config.dialect == "snowflake":
            datasource = SnowflakeDataSource(ds_config)
        else:
            raise DataSourceError(f"Unsupported dialect '{ds_config.dialect}' for datasource '{data_source_id}'")

        self._cache[data_source_id] = datasource
        return datasource

    def health_check(self, data_source_id: str) -> bool:
        datasource = self.get(data_source_id)
        return datasource.health_check()


__all__ = [
    "BaseDataSource",
    "SQLiteDataSource",
    "SnowflakeDataSource",
    "DataSourceFactory",
    "DataSourceError",
]
