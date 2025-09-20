"""Tests for Snowflake connection pooling and enterprise features."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.data.datasource import SnowflakeDataSource, SnowflakeConnectionPool, DataSourceError
from metadata_runtime.models import DataSourceConfig


class TestSnowflakeConnectionPool:
    """Test Snowflake connection pool functionality."""

    def test_pool_creation(self):
        """Test connection pool initialization."""
        connect_params = {"user": "test", "password": "test", "account": "test"}
        pool = SnowflakeConnectionPool(connect_params, max_connections=5)

        assert pool._max_connections == 5
        assert pool._max_idle_time == 300
        assert len(pool._connections) == 0

    @patch('snowflake.connector.connect')
    def test_get_connection_new(self, mock_connect):
        """Test getting a new connection from pool."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        connect_params = {"user": "test", "password": "test", "account": "test"}
        pool = SnowflakeConnectionPool(connect_params)

        conn = pool.get_connection()

        assert conn == mock_conn
        assert len(pool._connections) == 1
        assert pool._connections[mock_conn]['in_use'] is True
        mock_connect.assert_called_once_with(**connect_params)

    @patch('snowflake.connector.connect')
    def test_connection_reuse(self, mock_connect):
        """Test connection reuse from pool."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        connect_params = {"user": "test", "password": "test", "account": "test"}
        pool = SnowflakeConnectionPool(connect_params)

        # Get connection
        conn1 = pool.get_connection()
        pool.return_connection(conn1)

        # Get again - should reuse
        conn2 = pool.get_connection()

        assert conn1 == conn2
        assert len(pool._connections) == 1
        mock_connect.assert_called_once()  # Only called once

    def test_pool_exhaustion(self):
        """Test pool exhaustion handling."""
        connect_params = {"user": "test", "password": "test", "account": "test"}
        pool = SnowflakeConnectionPool(connect_params, max_connections=1)

        # Mock connection creation to fail
        with patch('snowflake.connector.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(DataSourceError, match="Failed to create Snowflake connection"):
                pool.get_connection()

    def test_connection_cleanup(self):
        """Test expired connection cleanup."""
        connect_params = {"user": "test", "password": "test", "account": "test"}
        pool = SnowflakeConnectionPool(connect_params, max_idle_time=0)  # Expire immediately

        mock_conn = Mock()
        with patch('snowflake.connector.connect', return_value=mock_conn):
            conn = pool.get_connection()
            pool.return_connection(conn)

            # Wait for expiration
            import time
            time.sleep(0.1)

            # Get new connection - should create new one
            conn2 = pool.get_connection()

            assert conn != conn2
            mock_conn.close.assert_called_once()


class TestSnowflakeDataSource:
    """Test enhanced Snowflake datasource."""

    @pytest.fixture
    def config(self):
        """Create test datasource config."""
        return DataSourceConfig(
            dialect="snowflake",
            dsn_env="TEST_SNOWFLAKE_DSN",
            role="ANALYST",
            warehouse="TEST_WH",
            database="TEST_DB",
            schema="TEST_SCHEMA"
        )

    def test_init_missing_dsn_env(self):
        """Test initialization with missing DSN env."""
        config = DataSourceConfig(dialect="snowflake")
        with pytest.raises(DataSourceError, match="requires 'dsn_env'"):
            SnowflakeDataSource(config)

    @patch.dict(os.environ, {"TEST_SNOWFLAKE_DSN": "user=test;password=test;account=test"})
    def test_connect_params_parsing(self, config):
        """Test DSN parsing and parameter building."""
        ds = SnowflakeDataSource(config)
        params = ds._connect_params()

        expected = {
            "user": "test",
            "password": "test",
            "account": "test",
            "role": "ANALYST",
            "warehouse": "TEST_WH",
            "database": "TEST_DB",
            "schema": "TEST_SCHEMA",
            "query_tag": "metadata_runtime_TEST_SNOWFLAKE_DSN",
            "application": "telecom_kpi_dashboard",
            "autocommit": True
        }
        assert params == expected

    @patch.dict(os.environ, {"TEST_SNOWFLAKE_DSN": "user=test;password=test;account=test"})
    def test_missing_env_var(self, config):
        """Test missing environment variable."""
        config.dsn_env = "MISSING_VAR"
        ds = SnowflakeDataSource(config)

        with pytest.raises(DataSourceError, match="not set"):
            ds._connect_params()

    @patch.dict(os.environ, {"TEST_SNOWFLAKE_DSN": "user=test;account=test"})  # Missing password
    def test_invalid_dsn(self, config):
        """Test invalid DSN format."""
        ds = SnowflakeDataSource(config)

        with pytest.raises(DataSourceError, match="must include 'user' and 'password'"):
            ds._connect_params()

    @patch('snowflake.connector.connect')
    @patch.dict(os.environ, {"TEST_SNOWFLAKE_DSN": "user=test;password=test;account=test"})
    def test_execute_with_pooling(self, mock_connect, config):
        """Test query execution with connection pooling."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock pandas read_sql
        with patch('pandas.read_sql') as mock_read_sql:
            mock_read_sql.return_value = Mock()
            mock_connect.return_value = mock_conn

            ds = SnowflakeDataSource(config)
            result = ds.execute("SELECT 1")

            # Verify connection pooling
            assert ds._pool is not None
            mock_read_sql.assert_called_once()

            # Verify query tagging
            call_args = mock_read_sql.call_args[0]
            assert "/* metadata_runtime_TEST_SNOWFLAKE_DSN */" in call_args[0]

    @patch('snowflake.connector.connect')
    @patch.dict(os.environ, {"TEST_SNOWFLAKE_DSN": "user=test;password=test;account=test"})
    def test_health_check_success(self, mock_connect, config):
        """Test successful health check."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        ds = SnowflakeDataSource(config)
        assert ds.health_check() is True

        mock_cursor.execute.assert_called_with("SELECT 1")

    @patch.dict(os.environ, {"TEST_SNOWFLAKE_DSN": "user=test;password=test;account=test"})
    def test_health_check_missing_connector(self, config):
        """Test health check when connector is not installed."""
        with patch.dict('sys.modules', {'snowflake': None}):
            ds = SnowflakeDataSource(config)
            assert ds.health_check() is False

    @patch('snowflake.connector.connect')
    @patch.dict(os.environ, {"TEST_SNOWFLAKE_DSN": "user=test;password=test;account=test"})
    def test_query_history(self, mock_connect, config):
        """Test query history retrieval."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        with patch('pandas.read_sql') as mock_read_sql:
            mock_read_sql.return_value = Mock()

            ds = SnowflakeDataSource(config)
            history = ds.get_query_history(limit=10)

            mock_read_sql.assert_called_once()
            call_args = mock_read_sql.call_args[0]
            assert "query_history()" in call_args[0]
            assert "metadata_runtime_TEST_SNOWFLAKE_DSN" in call_args[0]

    @patch.dict(os.environ, {"TEST_SNOWFLAKE_DSN": "user=test;password=test;account=test"})
    def test_pool_cleanup(self, config):
        """Test connection pool cleanup."""
        ds = SnowflakeDataSource(config)

        # Initialize pool
        ds._ensure_pool()
        assert ds._pool is not None

        # Close pool
        ds.close_pool()
        assert ds._pool is None


class TestSnowflakeIntegration:
    """Integration tests for Snowflake datasource (requires real Snowflake instance)."""

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("SNOWFLAKE_DSN"), reason="Requires SNOWFLAKE_DSN environment variable")
    def test_real_snowflake_connection(self, config):
        """Test real Snowflake connection (requires Snowflake instance)."""
        # This test would run against a real Snowflake instance
        # when SNOWFLAKE_DSN environment variable is set
        ds = SnowflakeDataSource(config)

        # Test health check
        assert ds.health_check() is True

        # Test simple query
        result = ds.execute("SELECT 1 as test_column")
        assert len(result) == 1
        assert result.iloc[0]['test_column'] == 1

        # Test query history
        history = ds.get_query_history(limit=5)
        assert isinstance(history, pd.DataFrame)
        assert len(history) <= 5

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("SNOWFLAKE_DSN"), reason="Requires SNOWFLAKE_DSN environment variable")
    def test_connection_pooling_under_load(self, config):
        """Test connection pooling under concurrent load."""
        import concurrent.futures
        import time

        ds = SnowflakeDataSource(config)

        def run_query():
            return ds.execute("SELECT 1 as test_column")

        # Run multiple queries concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_query) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 10
        for result in results:
            assert result.iloc[0]['test_column'] == 1

        # Verify pool efficiency
        if ds._pool:
            assert len(ds._pool._connections) <= 5  # Should reuse connections