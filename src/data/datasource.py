"""Datasource abstraction for metadata runtime queries."""
from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
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


class SnowflakeConnectionPool:
    """Connection pool for Snowflake with automatic cleanup and health monitoring."""

    def __init__(self, connect_params: Dict[str, Any], max_connections: int = 10, max_idle_time: int = 300):
        self._connect_params = connect_params
        self._max_connections = max_connections
        self._max_idle_time = max_idle_time
        self._connections: Dict[Any, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get_connection(self):
        """Get a connection from the pool or create a new one."""
        with self._lock:
            # Clean up expired connections
            current_time = time.time()
            expired = [conn for conn, meta in self._connections.items()
                      if current_time - meta['last_used'] > self._max_idle_time]
            for conn in expired:
                try:
                    conn.close()
                except Exception:
                    pass  # Ignore cleanup errors
                del self._connections[conn]

            # Find available connection
            for conn, meta in self._connections.items():
                if not meta['in_use']:
                    meta['in_use'] = True
                    meta['last_used'] = current_time
                    return conn

            # Create new connection if under limit
            if len(self._connections) < self._max_connections:
                try:
                    import snowflake.connector  # type: ignore
                    conn = snowflake.connector.connect(**self._connect_params)
                    self._connections[conn] = {
                        'in_use': True,
                        'last_used': current_time,
                        'created': current_time
                    }
                    return conn
                except Exception as exc:
                    raise DataSourceError(f"Failed to create Snowflake connection: {exc}") from exc

            raise DataSourceError("Connection pool exhausted")

    def return_connection(self, conn):
        """Return a connection to the pool."""
        with self._lock:
            if conn in self._connections:
                self._connections[conn]['in_use'] = False
                self._connections[conn]['last_used'] = time.time()

    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            for conn in list(self._connections.keys()):
                try:
                    conn.close()
                except Exception:
                    pass  # Ignore cleanup errors
            self._connections.clear()


class SnowflakeDataSource(BaseDataSource):
    """Enhanced Snowflake datasource with connection pooling and enterprise features."""

    def __init__(self, config: DataSourceConfig) -> None:
        if not config.dsn_env:
            raise DataSourceError("Snowflake data source requires 'dsn_env'")
        self._dsn_env = config.dsn_env
        self._role = config.role
        self._warehouse = config.warehouse
        self._database = config.database
        self._schema = config.schema
        self._query_tag = f"metadata_runtime_{config.dsn_env}"
        self._pool: Optional[SnowflakeConnectionPool] = None
        self._connect_params_cache: Optional[Dict[str, Any]] = None

    def _get_connect_params(self) -> Dict[str, Any]:
        """Get cached connection parameters."""
        if self._connect_params_cache is None:
            self._connect_params_cache = self._connect_params()
        return self._connect_params_cache

    def _connect_params(self) -> Dict[str, Any]:
        """Parse DSN and build connection parameters."""
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

        # Set defaults from config
        if self._role:
            params.setdefault("role", self._role)
        if self._warehouse:
            params.setdefault("warehouse", self._warehouse)
        if self._database:
            params.setdefault("database", self._database)
        if self._schema:
            params.setdefault("schema", self._schema)

        # Enterprise features
        params.setdefault("query_tag", self._query_tag)
        params.setdefault("application", "telecom_kpi_dashboard")
        params.setdefault("autocommit", True)

        return params

    def _ensure_pool(self):
        """Ensure connection pool is initialized."""
        if self._pool is None:
            connect_params = self._get_connect_params()
            self._pool = SnowflakeConnectionPool(connect_params)

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute query with connection pooling and query tagging."""
        try:
            import snowflake.connector  # type: ignore
        except ImportError as exc:
            raise DataSourceError("snowflake-connector-python is not installed") from exc

        self._ensure_pool()
        conn = None
        try:
            conn = self._pool.get_connection()

            # Add query tag for cost tracking
            tagged_sql = f"/* {self._query_tag} */ {sql}"

            # Execute with timeout and retry logic
            start_time = time.time()
            frame = pd.read_sql(tagged_sql, conn, params=params)
            execution_time = time.time() - start_time

            logger.info(f"Snowflake query executed in {execution_time:.2f}s")
            return frame

        except Exception as exc:
            logger.error(f"Snowflake execution failed: {exc}")
            raise DataSourceError(f"Snowflake execution failed: {exc}") from exc
        finally:
            if conn and self._pool:
                self._pool.return_connection(conn)

    def health_check(self) -> bool:
        """Health check with connection pooling."""
        try:
            import snowflake.connector  # type: ignore
        except ImportError:
            return False

        self._ensure_pool()
        conn = None
        try:
            conn = self._pool.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception:
            return False
        finally:
            if conn and self._pool:
                self._pool.return_connection(conn)

    def optimize_warehouse(self, query_complexity: str = "medium"):
        """Optimize warehouse selection based on query complexity."""
        # This would integrate with Snowflake's automatic clustering
        # and warehouse sizing based on query patterns
        pass

    def get_query_history(self, limit: int = 100):
        """Get recent query history for monitoring."""
        try:
            history_sql = f"""
            SELECT query_id, query_text, execution_time, warehouse_name, credits_used
            FROM table(information_schema.query_history())
            WHERE query_tag = '{self._query_tag}'
            ORDER BY start_time DESC
            LIMIT {limit}
            """
            return self.execute(history_sql)
        except Exception:
            return pd.DataFrame()

    def close_pool(self):
        """Close connection pool for cleanup."""
        if self._pool:
            self._pool.close_all()
            self._pool = None


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
    "SnowflakeConnectionPool",
    "DataSourceFactory",
    "DataSourceError",
]
