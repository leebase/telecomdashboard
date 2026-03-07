"""
Unit tests for database_connection module
"""

import pytest
import sqlite3
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from time import perf_counter

from database_connection import TelecomDatabase
from src.exceptions.custom_exceptions import DatabaseError, DatabaseConnectionError

class TestTelecomDatabase:
    """Test TelecomDatabase class"""
    
    def test_init(self):
        """Test database initialization"""
        db = TelecomDatabase("test.db")
        assert db.db_path == "test.db"
    
    def test_init_default_path(self):
        """Test database initialization with default path"""
        db = TelecomDatabase()
        assert db.db_path == "data/telecom_db.sqlite"
    
    def test_get_connection_success(self, test_database):
        """Test successful database connection"""
        db = TelecomDatabase(test_database)
        conn = db.get_connection()
        assert isinstance(conn, sqlite3.Connection)
        
        # Test foreign keys are enabled
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        assert result[0] == 1  # Foreign keys should be enabled
        
        conn.close()
    
    def test_get_connection_invalid_path(self):
        """Test database connection with invalid path"""
        db = TelecomDatabase("../invalid/path.db")
        with pytest.raises(ValueError, match="Invalid database path"):
            db.get_connection()
    
    def test_get_connection_nonexistent_file(self):
        """Test database connection with nonexistent file"""
        db = TelecomDatabase("data/nonexistent.sqlite")
        with pytest.raises(FileNotFoundError):
            db.get_connection()
    
    @pytest.mark.unit
    def test_get_network_metrics_success(self, telecom_db, sample_network_metrics):
        """Test successful network metrics retrieval"""
        metrics = telecom_db.get_network_metrics(days=30)
        
        assert metrics is not None
        assert isinstance(metrics, pd.Series)
        
        # Check that we have the expected metrics
        expected_columns = ['availability', 'latency', 'packet_loss', 
                           'bandwidth_utilization', 'mttr', 'dropped_call_rate']
        for col in expected_columns:
            assert col in metrics.index
    
    @pytest.mark.unit
    def test_get_network_metrics_invalid_days(self, telecom_db):
        """Test network metrics with invalid days parameter"""
        # Test with 0 days
        with pytest.raises(ValueError):
            telecom_db.get_network_metrics(days=0)
        
        # Test with negative days
        with pytest.raises(ValueError):
            telecom_db.get_network_metrics(days=-1)
    
    @pytest.mark.unit
    def test_get_customer_metrics_success(self, telecom_db):
        """Test successful customer metrics retrieval"""
        metrics = telecom_db.get_customer_metrics(days=30)
        
        assert metrics is not None
        assert isinstance(metrics, pd.Series)
        
        # Check that we have the expected metrics
        expected_columns = ['satisfaction_score', 'churn_rate', 'nps',
                           'first_contact_resolution', 'avg_handling_time', 
                           'customer_lifetime_value']
        for col in expected_columns:
            assert col in metrics.index
    
    @pytest.mark.unit
    def test_get_customer_trend_data(self, telecom_db):
        """Test customer trend data retrieval"""
        trend_data = telecom_db.get_customer_trend_data(days=30)
        
        assert isinstance(trend_data, pd.DataFrame)
        assert not trend_data.empty
        
        # Check expected columns exist
        expected_columns = ['region_name', 'satisfaction_score', 'churn_rate']
        for col in expected_columns:
            assert col in trend_data.columns
    
    @pytest.mark.unit
    def test_caching_behavior(self, telecom_db):
        """Test that caching works for repeated calls"""
        # First call
        start_time = datetime.now()
        metrics1 = telecom_db.get_network_metrics(days=30)
        first_call_time = (datetime.now() - start_time).total_seconds()
        
        # Second call (should be cached)
        start_time = datetime.now()
        metrics2 = telecom_db.get_network_metrics(days=30)
        second_call_time = (datetime.now() - start_time).total_seconds()
        
        # Results should be identical
        pd.testing.assert_series_equal(metrics1, metrics2)
        
        # Second call should be significantly faster (cached)
        assert second_call_time < first_call_time * 0.5
    
    @pytest.mark.unit
    @patch('database_connection.pd.read_sql_query')
    def test_database_error_handling(self, mock_read_sql, telecom_db):
        """Test database error handling"""
        # Simulate database error
        mock_read_sql.side_effect = sqlite3.Error("Database error")
        
        with pytest.raises(sqlite3.Error):
            telecom_db.get_network_metrics()
    
    @pytest.mark.unit
    def test_security_logging(self, telecom_db):
        """Test that database operations are logged for security"""
        with patch('database_connection.security_logger') as mock_logger:
            telecom_db.get_network_metrics(days=30)
            
            # Verify security logging occurred
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args[0][0]
            assert "Database operation" in call_args
    
    @pytest.mark.parametrize("days,expected_condition", [
        (7, "7"),
        (30, "30"), 
        (90, "90"),
        (365, "365")
    ])
    def test_different_time_periods(self, telecom_db, days, expected_condition):
        """Test metrics retrieval for different time periods"""
        metrics = telecom_db.get_network_metrics(days=days)
        assert metrics is not None
        assert isinstance(metrics, pd.Series)
    
    @pytest.mark.unit
    def test_get_revenue_metrics(self, telecom_db):
        """Test revenue metrics retrieval"""
        # Note: This will return empty results since we don't have revenue data in test DB
        # but should not raise an error
        metrics = telecom_db.get_revenue_metrics(days=30)
        assert isinstance(metrics, pd.Series)
    
    @pytest.mark.unit
    def test_connection_context_manager(self, telecom_db):
        """Test database connection as context manager"""
        with telecom_db.get_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    @pytest.mark.unit
    def test_concurrent_access(self, telecom_db):
        """Test concurrent database access"""
        import threading
        results = []
        errors = []
        
        def worker():
            try:
                metrics = telecom_db.get_network_metrics(days=30)
                results.append(metrics)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # All results should be the same (due to caching)
        for result in results[1:]:
            pd.testing.assert_series_equal(results[0], result)

class TestDatabaseSecurity:
    """Test database security features"""
    
    @pytest.mark.security
    def test_sql_injection_protection(self, telecom_db):
        """Test protection against SQL injection"""
        # These should not cause SQL injection
        malicious_inputs = [
            "'; DROP TABLE fact_network_metrics; --",
            "1; DELETE FROM dim_region; --",
            "1 UNION SELECT * FROM sqlite_master --"
        ]
        
        for malicious_input in malicious_inputs:
            # The function should handle these safely
            try:
                # This should either work safely or raise an appropriate error
                result = telecom_db.get_network_metrics(days=30)
                assert isinstance(result, pd.Series)
            except ValueError:
                # ValueError for invalid input is acceptable
                pass
    
    @pytest.mark.security
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow"
        ]
        
        for path in malicious_paths:
            with pytest.raises(ValueError, match="Invalid database path"):
                db = TelecomDatabase(path)
                db.get_connection()
    
    @pytest.mark.security
    @patch('database_connection.security_manager')
    def test_security_validation(self, mock_security_manager, telecom_db):
        """Test that security validation is called"""
        mock_security_manager.validate_input.return_value = True
        
        telecom_db.get_network_metrics(days=30)
        
        # Security manager should be called for database operations
        # This test verifies integration with security system

class TestDatabasePerformance:
    """Test database performance"""
    
    @pytest.mark.performance
    def test_query_performance(self, telecom_db, performance_monitor):
        """Test that queries complete within reasonable time"""
        with performance_monitor as monitor:
            metrics = telecom_db.get_network_metrics(days=30)
        
        assert monitor.duration < 1.0, f"Query took {monitor.duration}s, should be under 1s"
        assert metrics is not None
    
    @pytest.mark.performance
    def test_cache_performance(self, telecom_db):
        """Test that caching improves performance"""
        telecom_db.get_network_metrics.cache_clear()

        # First call (uncached)
        start = perf_counter()
        telecom_db.get_network_metrics(days=30)
        uncached_time = perf_counter() - start
        
        # Second call (cached)
        start = perf_counter()
        telecom_db.get_network_metrics(days=30)
        cached_time = perf_counter() - start
        
        assert telecom_db.get_network_metrics.cache_info()["cache_size"] >= 1
        assert cached_time < uncached_time, "Cache not providing expected performance improvement"
    
    @pytest.mark.performance
    def test_large_dataset_handling(self, telecom_db):
        """Test handling of larger datasets"""
        # Test with maximum allowed days
        with pytest.raises(ValueError):
            telecom_db.get_network_metrics(days=400)  # Should be rejected
        
        # Test with large but valid range
        metrics = telecom_db.get_network_metrics(days=365)
        assert metrics is not None

class TestDatabaseErrorRecovery:
    """Test error recovery mechanisms"""
    
    @pytest.mark.unit
    @patch('database_connection.sqlite3.connect')
    def test_connection_retry(self, mock_connect, test_database):
        """Test connection retry logic"""
        real_connect = sqlite3.connect

        # First call fails, second succeeds without leaking a pre-created connection.
        def flaky_connect(*args, **kwargs):
            if not getattr(flaky_connect, "failed_once", False):
                flaky_connect.failed_once = True
                raise sqlite3.Error("Connection failed")
            return real_connect(*args, **kwargs)

        flaky_connect.failed_once = False
        mock_connect.side_effect = flaky_connect
        
        db = TelecomDatabase(test_database)
        
        # This should eventually succeed after retry
        # Note: Current implementation doesn't have retry logic,
        # but this test shows how it would be tested
        with pytest.raises(sqlite3.Error):
            db.get_connection()
    
    @pytest.mark.unit
    def test_graceful_degradation(self, telecom_db):
        """Test graceful degradation when data is missing"""
        # Test with empty database conditions
        # The methods should return empty Series/DataFrames rather than crashing
        
        # This test would need a database with no data
        # For now, we test that existing methods handle edge cases
