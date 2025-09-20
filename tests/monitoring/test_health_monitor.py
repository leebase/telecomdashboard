"""Tests for health monitoring and alerting system."""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.monitoring.health_monitor import (
    HealthStatus, ComponentStatus, HealthCheckResult, SystemMetrics,
    HealthChecker, MetricsCollector, AlertManager,
    create_database_health_check, create_filesystem_health_check,
    create_memory_health_check
)


class TestHealthCheckResult:
    """Test HealthCheckResult class."""

    def test_health_check_result_creation(self):
        """Test health check result creation."""
        result = HealthCheckResult(
            component="test_component",
            status=ComponentStatus.OK,
            message="Test message",
            details={"key": "value"},
            timestamp=datetime.now(),
            response_time=1.5
        )

        assert result.component == "test_component"
        assert result.status == ComponentStatus.OK
        assert result.message == "Test message"
        assert result.details == {"key": "value"}
        assert result.response_time == 1.5

    def test_health_check_result_to_dict(self):
        """Test converting health check result to dictionary."""
        timestamp = datetime.now()
        result = HealthCheckResult(
            component="test_component",
            status=ComponentStatus.OK,
            message="Test message",
            details={"key": "value"},
            timestamp=timestamp,
            response_time=1.5
        )

        data = result.to_dict()

        assert data["component"] == "test_component"
        assert data["status"] == "ok"
        assert data["message"] == "Test message"
        assert data["response_time"] == 1.5
        assert "timestamp" in data


class TestSystemMetrics:
    """Test SystemMetrics class."""

    def test_system_metrics_creation(self):
        """Test system metrics creation."""
        metrics = SystemMetrics(
            cpu_percent=45.2,
            memory_percent=67.8,
            disk_usage_percent=78.9,
            network_connections=150,
            thread_count=25,
            open_files=45,
            uptime_seconds=3600.5
        )

        assert metrics.cpu_percent == 45.2
        assert metrics.memory_percent == 67.8
        assert metrics.disk_usage_percent == 78.9
        assert metrics.network_connections == 150
        assert metrics.thread_count == 25
        assert metrics.open_files == 45
        assert metrics.uptime_seconds == 3600.5

    def test_system_metrics_to_dict(self):
        """Test converting system metrics to dictionary."""
        metrics = SystemMetrics(
            cpu_percent=45.2,
            memory_percent=67.8,
            disk_usage_percent=78.9,
            network_connections=150,
            thread_count=25,
            open_files=45,
            uptime_seconds=3600.5
        )

        data = metrics.to_dict()

        assert data["cpu_percent"] == 45.2
        assert data["memory_percent"] == 67.8
        assert data["network_connections"] == 150


class TestHealthChecker:
    """Test HealthChecker functionality."""

    def test_health_checker_initialization(self):
        """Test health checker initialization."""
        checker = HealthChecker(check_interval=30)

        assert checker.check_interval == 30
        assert len(checker.checks) == 0
        assert len(checker.last_results) == 0

    def test_register_and_unregister_check(self):
        """Test registering and unregistering health checks."""
        checker = HealthChecker()

        def dummy_check():
            return HealthCheckResult(
                component="dummy",
                status=ComponentStatus.OK,
                message="OK",
                details={},
                timestamp=datetime.now(),
                response_time=0.0
            )

        # Register check
        checker.register_check("dummy", dummy_check)
        assert "dummy" in checker.checks

        # Unregister check
        checker.unregister_check("dummy")
        assert "dummy" not in checker.checks

    def test_run_check_success(self):
        """Test running a successful health check."""
        checker = HealthChecker()

        def success_check():
            return HealthCheckResult(
                component="success",
                status=ComponentStatus.OK,
                message="Success",
                details={"result": "good"},
                timestamp=datetime.now(),
                response_time=0.0
            )

        checker.register_check("success", success_check)
        result = checker.run_check("success")

        assert result is not None
        assert result.component == "success"
        assert result.status == ComponentStatus.OK
        assert result.message == "Success"
        assert "success" in checker.last_results

    def test_run_check_failure(self):
        """Test running a failing health check."""
        checker = HealthChecker()

        def failing_check():
            raise Exception("Check failed")

        checker.register_check("failing", failing_check)
        result = checker.run_check("failing")

        assert result is not None
        assert result.component == "failing"
        assert result.status == ComponentStatus.ERROR
        assert "Check failed" in result.message

    def test_run_all_checks(self):
        """Test running all health checks."""
        checker = HealthChecker()

        def check1():
            return HealthCheckResult(
                component="check1",
                status=ComponentStatus.OK,
                message="OK",
                details={},
                timestamp=datetime.now(),
                response_time=0.0
            )

        def check2():
            return HealthCheckResult(
                component="check2",
                status=ComponentStatus.WARNING,
                message="Warning",
                details={},
                timestamp=datetime.now(),
                response_time=0.0
            )

        checker.register_check("check1", check1)
        checker.register_check("check2", check2)

        results = checker.run_all_checks()

        assert len(results) == 2
        assert "check1" in results
        assert "check2" in results
        assert results["check1"].status == ComponentStatus.OK
        assert results["check2"].status == ComponentStatus.WARNING

    def test_get_overall_health(self):
        """Test getting overall health status."""
        checker = HealthChecker()

        # No results yet
        assert checker.get_overall_health() == HealthStatus.UNHEALTHY

        # Add some results
        checker.last_results = {
            "check1": HealthCheckResult(
                component="check1",
                status=ComponentStatus.OK,
                message="OK",
                details={},
                timestamp=datetime.now(),
                response_time=0.0
            ),
            "check2": HealthCheckResult(
                component="check2",
                status=ComponentStatus.WARNING,
                message="Warning",
                details={},
                timestamp=datetime.now(),
                response_time=0.0
            )
        }

        assert checker.get_overall_health() == HealthStatus.DEGRADED

    def test_get_health_summary(self):
        """Test getting health summary."""
        checker = HealthChecker()

        # Add mock results
        checker.last_results = {
            "check1": HealthCheckResult(
                component="check1",
                status=ComponentStatus.OK,
                message="OK",
                details={},
                timestamp=datetime.now(),
                response_time=0.0
            ),
            "check2": HealthCheckResult(
                component="check2",
                status=ComponentStatus.ERROR,
                message="Error",
                details={},
                timestamp=datetime.now(),
                response_time=0.0
            )
        }

        summary = checker.get_health_summary()

        assert summary["status"] == "unhealthy"
        assert summary["total_checks"] == 2
        assert summary["healthy_checks"] == 1
        assert summary["error_checks"] == 1
        assert "timestamp" in summary
        assert "checks" in summary

    def test_alert_callback(self):
        """Test alert callback functionality."""
        checker = HealthChecker()
        alert_calls = []

        def alert_callback(result):
            alert_calls.append(result)

        checker.add_alert_callback(alert_callback)

        def warning_check():
            return HealthCheckResult(
                component="warning_check",
                status=ComponentStatus.WARNING,
                message="Warning",
                details={},
                timestamp=datetime.now(),
                response_time=0.0
            )

        checker.register_check("warning_check", warning_check)
        checker.run_check("warning_check")

        assert len(alert_calls) == 1
        assert alert_calls[0].component == "warning_check"
        assert alert_calls[0].status == ComponentStatus.WARNING


class TestMetricsCollector:
    """Test MetricsCollector functionality."""

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_connections')
    @patch('threading.active_count')
    @patch('psutil.Process')
    def test_collect_system_metrics(self, mock_process, mock_net, mock_disk, mock_memory, mock_cpu, mock_threading):
        """Test collecting system metrics."""
        # Mock psutil functions
        mock_cpu.return_value = 45.2
        mock_memory.return_value = Mock(percent=67.8)
        mock_disk.return_value = Mock(percent=78.9)
        mock_net.return_value = [Mock()] * 10  # 10 connections
        mock_threading.return_value = 25

        # Mock process open files
        mock_process_instance = Mock()
        mock_process_instance.open_files.return_value = [Mock()] * 15
        mock_process.return_value = mock_process_instance

        collector = MetricsCollector()
        metrics = collector.collect_system_metrics()

        assert metrics.cpu_percent == 45.2
        assert metrics.memory_percent == 67.8
        assert metrics.disk_usage_percent == 78.9
        assert metrics.network_connections == 10
        assert metrics.thread_count == 25
        assert metrics.open_files == 15
        assert metrics.uptime_seconds > 0

        # Check history
        assert len(collector.metrics_history) == 1

    def test_get_metrics_history(self):
        """Test getting metrics history."""
        collector = MetricsCollector()

        # Add some mock metrics
        metrics1 = SystemMetrics(10, 20, 30, 40, 50, 60, 70)
        metrics2 = SystemMetrics(11, 21, 31, 41, 51, 61, 71)

        collector.metrics_history = [metrics1, metrics2]

        history = collector.get_metrics_history(limit=1)
        assert len(history) == 1
        assert history[0] == metrics2

    def test_get_average_metrics(self):
        """Test getting average metrics."""
        collector = MetricsCollector()

        # Add mock metrics
        metrics1 = SystemMetrics(10, 20, 30, 40, 50, 60, 70)
        metrics2 = SystemMetrics(20, 30, 40, 50, 60, 70, 80)

        collector.metrics_history = [metrics1, metrics2]

        avg_metrics = collector.get_average_metrics(minutes=1)

        assert avg_metrics is not None
        assert avg_metrics.cpu_percent == 15.0  # (10+20)/2
        assert avg_metrics.memory_percent == 25.0  # (20+30)/2


class TestAlertManager:
    """Test AlertManager functionality."""

    def test_alert_manager_initialization(self):
        """Test alert manager initialization."""
        manager = AlertManager()

        assert len(manager.alerts) == 0
        assert len(manager.alert_handlers) == 0

    def test_add_alert_handler(self):
        """Test adding alert handler."""
        manager = AlertManager()

        def handler(alert):
            pass

        manager.add_alert_handler(handler)
        assert len(manager.alert_handlers) == 1

    def test_trigger_alert(self):
        """Test triggering alert."""
        manager = AlertManager()
        alerts_received = []

        def handler(alert):
            alerts_received.append(alert)

        manager.add_alert_handler(handler)

        manager.trigger_alert(
            alert_type="test",
            severity="warning",
            message="Test alert",
            details={"key": "value"}
        )

        assert len(manager.alerts) == 1
        assert len(alerts_received) == 1

        alert = manager.alerts[0]
        assert alert["type"] == "test"
        assert alert["severity"] == "warning"
        assert alert["message"] == "Test alert"
        assert alert["details"] == {"key": "value"}
        assert "id" in alert
        assert "timestamp" in alert
        assert alert["acknowledged"] is False

    def test_get_active_alerts(self):
        """Test getting active alerts."""
        manager = AlertManager()

        manager.trigger_alert("test1", "info", "Alert 1")
        manager.trigger_alert("test2", "warning", "Alert 2")

        active = manager.get_active_alerts()
        assert len(active) == 2

        # Acknowledge one
        manager.acknowledge_alert(manager.alerts[0]["id"])

        active = manager.get_active_alerts()
        assert len(active) == 1
        assert active[0]["message"] == "Alert 2"

    def test_get_alert_summary(self):
        """Test getting alert summary."""
        manager = AlertManager()

        manager.trigger_alert("type1", "info", "Alert 1")
        manager.trigger_alert("type1", "warning", "Alert 2")
        manager.trigger_alert("type2", "error", "Alert 3")

        summary = manager.get_alert_summary()

        assert summary["total_alerts"] == 3
        assert summary["active_alerts"] == 3
        assert summary["severity_breakdown"]["info"] == 1
        assert summary["severity_breakdown"]["warning"] == 1
        assert summary["severity_breakdown"]["error"] == 1
        assert summary["type_breakdown"]["type1"] == 2
        assert summary["type_breakdown"]["type2"] == 1


class TestBuiltInHealthChecks:
    """Test built-in health check functions."""

    @patch('sqlite3.connect')
    def test_database_health_check_success(self, mock_connect):
        """Test successful database health check."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        check_func = create_database_health_check("test.db")
        result = check_func()

        assert result.component == "database"
        assert result.status == ComponentStatus.OK
        assert "successful" in result.message
        mock_cursor.execute.assert_called_with("SELECT 1")

    @patch('sqlite3.connect')
    def test_database_health_check_failure(self, mock_connect):
        """Test failing database health check."""
        mock_connect.side_effect = Exception("Connection failed")

        check_func = create_database_health_check("test.db")
        result = check_func()

        assert result.component == "database"
        assert result.status == ComponentStatus.ERROR
        assert "failed" in result.message

    @patch('psutil.disk_usage')
    def test_filesystem_health_check_normal(self, mock_disk):
        """Test normal filesystem health check."""
        mock_disk.return_value = Mock(percent=50.0)

        check_func = create_filesystem_health_check()
        result = check_func()

        assert result.component == "filesystem"
        assert result.status == ComponentStatus.OK
        assert "normal" in result.message

    @patch('psutil.disk_usage')
    def test_filesystem_health_check_warning(self, mock_disk):
        """Test warning filesystem health check."""
        mock_disk.return_value = Mock(percent=85.0)

        check_func = create_filesystem_health_check()
        result = check_func()

        assert result.component == "filesystem"
        assert result.status == ComponentStatus.WARNING
        assert "high" in result.message

    @patch('psutil.disk_usage')
    def test_filesystem_health_check_error(self, mock_disk):
        """Test error filesystem health check."""
        mock_disk.return_value = Mock(percent=95.0)

        check_func = create_filesystem_health_check()
        result = check_func()

        assert result.component == "filesystem"
        assert result.status == ComponentStatus.ERROR
        assert "critical" in result.message

    @patch('psutil.virtual_memory')
    def test_memory_health_check_normal(self, mock_memory):
        """Test normal memory health check."""
        mock_memory.return_value = Mock(percent=50.0)

        check_func = create_memory_health_check()
        result = check_func()

        assert result.component == "memory"
        assert result.status == ComponentStatus.OK
        assert "normal" in result.message


@pytest.mark.integration
class TestHealthMonitorIntegration:
    """Integration tests for health monitoring system."""

    def test_full_health_check_workflow(self):
        """Test complete health check workflow."""
        from src.monitoring.health_monitor import health_checker

        # Run all checks
        results = health_checker.run_all_checks()

        # Should have at least the default checks
        assert len(results) >= 3  # database, filesystem, memory

        # Get overall health
        overall = health_checker.get_overall_health()
        assert overall in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]

        # Get summary
        summary = health_checker.get_health_summary()
        assert "status" in summary
        assert "checks" in summary
        assert summary["total_checks"] >= 3

    def test_metrics_collection_workflow(self):
        """Test metrics collection workflow."""
        from src.monitoring.health_monitor import metrics_collector

        # Collect metrics
        metrics = metrics_collector.collect_system_metrics()

        assert isinstance(metrics, SystemMetrics)
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0

        # Get history
        history = metrics_collector.get_metrics_history()
        assert len(history) >= 1

    def test_alert_workflow(self):
        """Test alert workflow."""
        from src.monitoring.health_monitor import alert_manager

        alerts_received = []

        def test_handler(alert):
            alerts_received.append(alert)

        alert_manager.add_alert_handler(test_handler)

        # Trigger alert
        alert_manager.trigger_alert(
            alert_type="test",
            severity="info",
            message="Test alert"
        )

        # Check alert was created and handler called
        assert len(alert_manager.alerts) == 1
        assert len(alerts_received) == 1
        assert alerts_received[0]["message"] == "Test alert"

        # Check summary
        summary = alert_manager.get_alert_summary()
        assert summary["total_alerts"] == 1
        assert summary["active_alerts"] == 1