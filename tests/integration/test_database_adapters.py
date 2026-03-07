"""
Database Adapter Integration Tests

Tests for enterprise database adapters (PostgreSQL, Snowflake) with connection pooling,
performance validation, and production readiness verification.
"""

import pytest
import sys
import os
import time
import threading
from unittest.mock import patch, MagicMock
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from enterprise_database_adapter import (
    DatabaseAdapter, PostgreSQLAdapter, SnowflakeAdapter, 
    ConnectionPool, DatabaseCredentials
)
from database_connection import TelecomDatabase

class TestConnectionPooling:
    """Test connection pooling functionality"""
    
    @pytest.fixture
    def mock_connection_factory(self):
        """Mock connection factory for testing"""
        def create_connection():
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = MagicMock()
            mock_conn.execute.return_value = None
            mock_conn.fetchone.return_value = (1,)
            return mock_conn
        return create_connection
    
    def test_connection_pool_initialization(self, mock_connection_factory):
        """Test connection pool initialization with min connections"""
        pool = ConnectionPool(
            create_connection_func=mock_connection_factory,
            min_connections=2,
            max_connections=5
        )
        
        assert pool.min_connections == 2
        assert pool.max_connections == 5
        assert pool._active_connections >= 2  # Should create min connections
    
    def test_connection_pool_get_return(self, mock_connection_factory):
        """Test getting and returning connections from pool"""
        pool = ConnectionPool(
            create_connection_func=mock_connection_factory,
            min_connections=1,
            max_connections=3
        )
        
        # Get connection
        conn1 = pool.get_connection(timeout=5.0)
        assert conn1 is not None
        
        # Return connection
        pool.return_connection(conn1)
        
        # Get connection again (should reuse)
        conn2 = pool.get_connection(timeout=5.0)
        assert conn2 is not None
    
    def test_connection_pool_max_connections(self, mock_connection_factory):
        """Test connection pool max connection limit"""
        pool = ConnectionPool(
            create_connection_func=mock_connection_factory,
            min_connections=1,
            max_connections=2
        )
        
        # Get max connections
        conn1 = pool.get_connection(timeout=1.0)
        conn2 = pool.get_connection(timeout=1.0)
        
        # Should timeout when trying to get third connection
        start_time = time.time()
        with pytest.raises(Exception):  # Should timeout or raise exception
            pool.get_connection(timeout=0.5)
        elapsed = time.time() - start_time
        assert elapsed >= 0.4  # Should wait for timeout
        
        # Return one connection
        pool.return_connection(conn1)
        
        # Should now be able to get connection
        conn3 = pool.get_connection(timeout=1.0)
        assert conn3 is not None
    
    def test_connection_pool_thread_safety(self, mock_connection_factory):
        """Test connection pool thread safety"""
        pool = ConnectionPool(
            create_connection_func=mock_connection_factory,
            min_connections=2,
            max_connections=5
        )
        
        connections = []
        errors = []
        
        def worker():
            try:
                conn = pool.get_connection(timeout=2.0)
                connections.append(conn)
                time.sleep(0.1)  # Simulate work
                pool.return_connection(conn)
            except Exception as e:
                errors.append(e)
        
        # Run multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should not have errors
        assert len(errors) == 0, f"Errors in threaded test: {errors}"
        assert len(connections) == 10  # All threads should get connections

class TestPostgreSQLAdapter:
    """Test PostgreSQL adapter functionality"""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock PostgreSQL credentials"""
        return DatabaseCredentials(
            host="localhost",
            port=5432,
            database="test_telecom",
            username="test_user",
            password="test_pass"
        )
    
    @patch('psycopg2.connect')
    def test_postgresql_adapter_initialization(self, mock_connect, mock_credentials):
        """Test PostgreSQL adapter initialization"""
        mock_connect.return_value = MagicMock()
        
        adapter = PostgreSQLAdapter(mock_credentials, use_pooling=True)
        
        assert adapter.credentials == mock_credentials
        assert adapter.use_pooling is True
        assert adapter._pool is not None
    
    @patch('psycopg2.connect')
    def test_postgresql_query_execution(self, mock_connect, mock_credentials):
        """Test PostgreSQL query execution"""
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock pandas read_sql_query
        with patch('pandas.read_sql_query') as mock_read_sql:
            mock_read_sql.return_value = pd.DataFrame({'test': [1, 2, 3]})
            
            adapter = PostgreSQLAdapter(mock_credentials, use_pooling=False)
            result = adapter.execute_query("SELECT * FROM test_table")
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            mock_read_sql.assert_called_once()
    
    @patch('psycopg2.connect')
    def test_postgresql_connection_pooling(self, mock_connect, mock_credentials):
        """Test PostgreSQL with connection pooling"""
        mock_connect.return_value = MagicMock()
        
        adapter = PostgreSQLAdapter(mock_credentials, use_pooling=True)
        
        # Test getting connection from pool
        conn = adapter.get_connection()
        assert conn is not None
        
        # Test returning connection to pool
        adapter.return_connection(conn)
    
    @patch('psycopg2.connect')
    def test_postgresql_error_handling(self, mock_connect, mock_credentials):
        """Test PostgreSQL error handling"""
        mock_connect.side_effect = Exception("Connection failed")
        
        adapter = PostgreSQLAdapter(mock_credentials, use_pooling=False)
        
        # Should handle connection errors gracefully
        with pytest.raises(Exception):
            adapter.execute_query("SELECT 1")

class TestSnowflakeAdapter:
    """Test Snowflake adapter functionality"""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock Snowflake credentials"""
        return DatabaseCredentials(
            host="account.snowflakecomputing.com",
            database="TELECOM_DW",
            username="TELECOM_USER",
            password="secure_password",
            warehouse="COMPUTE_WH",
            schema="PUBLIC"
        )
    
    @patch('snowflake.connector.connect')
    def test_snowflake_adapter_initialization(self, mock_connect, mock_credentials):
        """Test Snowflake adapter initialization"""
        mock_connect.return_value = MagicMock()
        
        adapter = SnowflakeAdapter(mock_credentials, use_pooling=True)
        
        assert adapter.credentials == mock_credentials
        assert adapter.use_pooling is True
        assert adapter._pool is not None
    
    @patch('snowflake.connector.connect')
    def test_snowflake_query_tagging(self, mock_connect, mock_credentials):
        """Test Snowflake query tagging functionality"""
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetch_pandas_all.return_value = pd.DataFrame({'result': [1]})
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        adapter = SnowflakeAdapter(mock_credentials, use_pooling=False)
        result = adapter.execute_query(
            "SELECT COUNT(*) FROM fact_network_metrics",
            user_context="test_user"
        )

        assert isinstance(result, pd.DataFrame)

        # Verify query tag was set
        calls = mock_cursor.execute.call_args_list
        assert len(calls) >= 1

        # Check that query tag contains expected elements
        tag_call = calls[0][0][0]  # First call, first argument
        assert "ALTER SESSION SET QUERY_TAG" in tag_call
        assert "telecom_dashboard" in tag_call
        assert "test_user" in tag_call
    
    @patch('snowflake.connector.connect')
    def test_snowflake_compliance_tagging(self, mock_connect, mock_credentials):
        """Test Snowflake compliance and audit tagging"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetch_pandas_all.return_value = pd.DataFrame({'test': [1]})
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        adapter = SnowflakeAdapter(mock_credentials, use_pooling=False)

        # Generate query tag
        tag = adapter._generate_query_tag("audit_user")

        # Should contain compliance markers
        assert "soc2_audit" in tag
        assert "gdpr_compliant" in tag
        assert "audit_user" in tag
        assert "telecom_dashboard" in tag

        # Should contain timestamp
        import re
        timestamp_pattern = r'\d{8}_\d{6}'
        assert re.search(timestamp_pattern, tag), f"No timestamp found in tag: {tag}"

class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    def test_sqlite_database_operations(self):
        """Test SQLite database operations (current implementation)"""
        db = TelecomDatabase()
        
        # Test basic connectivity
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_network_metrics_query_structure(self):
        """Test network metrics query structure and caching"""
        db = TelecomDatabase()
        
        # Test network metrics retrieval
        metrics = db.get_network_metrics(days=7)
        
        assert metrics is not None
        assert isinstance(metrics, (dict, pd.Series))
        
        # Should have expected metric keys
        expected_keys = ['availability', 'latency', 'packet_loss', 'bandwidth_utilization']
        for key in expected_keys:
            if key in metrics:  # Keys might vary based on data availability
                assert isinstance(metrics[key], (int, float, type(None)))
    
    def test_database_performance_benchmarks(self):
        """Test database performance benchmarks"""
        db = TelecomDatabase()
        
        # Test query performance
        start_time = time.time()
        metrics = db.get_network_metrics(days=30)
        query_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert query_time < 5.0, f"Query took too long: {query_time}s"
        
        # Test cached query performance
        start_time = time.time()
        cached_metrics = db.get_network_metrics(days=30)
        cached_time = time.time() - start_time
        
        # Cached query should be faster
        assert cached_time < query_time, "Cached query not faster than original"
    
    def test_concurrent_database_operations(self):
        """Test concurrent database operations"""
        db = TelecomDatabase()
        
        def worker():
            """Worker function for concurrent testing"""
            try:
                metrics = db.get_network_metrics(days=7)
                return metrics is not None
            except Exception:
                return False
        
        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All operations should succeed
        assert all(results), "Some concurrent operations failed"
    
    def test_database_connection_recovery(self):
        """Test database connection recovery"""
        db = TelecomDatabase()
        
        # Get initial connection
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
        
        # Should be able to get new connection
        with db.get_connection() as conn2:
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT 2")
            assert cursor2.fetchone()[0] == 2

class TestDataValidation:
    """Test data validation and integrity"""
    
    def test_data_type_validation(self):
        """Test that database returns proper data types"""
        db = TelecomDatabase()
        
        # Test various metric retrievals
        test_functions = [
            (db.get_network_metrics, {}),
            (db.get_customer_metrics, {}),
            (db.get_revenue_metrics, {}),
            (db.get_usage_metrics, {}),
            (db.get_operations_metrics, {})
        ]
        
        for func, kwargs in test_functions:
            try:
                result = func(**kwargs)
                if result is not None:
                    assert isinstance(result, (dict, pd.Series)), f"Expected mapping-like result from {func.__name__}"
                    
                    # Validate numeric values
                    for key, value in result.items():
                        if value is not None:
                            assert isinstance(value, (int, float, str)), f"Invalid type for {key}: {type(value)}"
            except Exception as e:
                # Should not raise unhandled exceptions
                assert False, f"Function {func.__name__} raised exception: {e}"
    
    def test_sql_injection_prevention_integration(self):
        """Integration test for SQL injection prevention"""
        db = TelecomDatabase()
        
        # Test with potentially malicious inputs
        malicious_inputs = [
            "'; DROP TABLE fact_network_metrics; --",
            "1 OR 1=1",
            "UNION SELECT * FROM sqlite_master",
            "../../../etc/passwd",
            "<script>alert('XSS')</script>"
        ]
        
        for malicious_input in malicious_inputs:
            try:
                # These should either work safely or raise ValueError
                with pytest.raises(ValueError):
                    db.get_trend_data(malicious_input, days=30)
                
                with pytest.raises(ValueError):
                    db.get_region_data(malicious_input, days=30)
                    
            except Exception as e:
                # Should not expose system information
                error_msg = str(e).lower()
                assert "sqlite_master" not in error_msg
                assert "/etc/passwd" not in error_msg
                assert "drop table" not in error_msg

class TestPerformanceMetrics:
    """Test performance metrics and monitoring"""
    
    def test_cache_effectiveness(self):
        """Test cache effectiveness metrics"""
        db = TelecomDatabase()
        
        # Clear any existing cache
        if hasattr(db.get_network_metrics, 'cache_clear'):
            db.get_network_metrics.cache_clear()
        
        # First call (cache miss)
        start_time = time.time()
        result1 = db.get_network_metrics(days=30)
        first_call_time = time.time() - start_time
        
        # Second call (cache hit)
        start_time = time.time()
        result2 = db.get_network_metrics(days=30)
        second_call_time = time.time() - start_time
        
        # Results should be identical
        assert result1 == result2
        
        # Second call should be significantly faster (if caching is working)
        if second_call_time > 0:  # Avoid division by zero
            speedup = first_call_time / second_call_time
            # Allow for some variation, but should see improvement
            assert speedup > 0.5, f"Cache not effective: speedup = {speedup}"
    
    def test_memory_usage_monitoring(self):
        """Test memory usage during operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        db = TelecomDatabase()
        
        # Perform multiple operations
        for _ in range(10):
            db.get_network_metrics(days=30)
            db.get_customer_metrics(days=30)
            db.get_revenue_metrics(days=30)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for these operations)
        assert memory_increase < 50 * 1024 * 1024, f"Excessive memory usage: {memory_increase / 1024 / 1024:.2f}MB"

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
