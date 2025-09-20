"""Tests for audit logging system."""

import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.security.audit_logger import (
    AuditEventType, AuditSeverity, AuditEvent, AuditLogger,
    AuditLogAnalyzer, audit_metadata_change, audit_query_execution,
    audit_permission_denied, get_audit_logger, init_audit_logger
)


class TestAuditEvent:
    """Test AuditEvent class."""

    def test_audit_event_creation(self):
        """Test audit event creation."""
        event = AuditEvent(
            event_id="test_123",
            event_type=AuditEventType.QUERY_EXECUTION,
            severity=AuditSeverity.INFO,
            timestamp=1234567890.0,
            user_id="user123",
            username="testuser",
            session_id="session123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            resource="dashboard",
            action="view",
            details={"key": "value"},
            metadata={"extra": "data"}
        )

        assert event.event_id == "test_123"
        assert event.event_type == AuditEventType.QUERY_EXECUTION
        assert event.severity == AuditSeverity.INFO
        assert event.user_id == "user123"
        assert event.details == {"key": "value"}

    def test_audit_event_to_dict(self):
        """Test converting audit event to dictionary."""
        event = AuditEvent(
            event_id="test_123",
            event_type=AuditEventType.USER_LOGIN,
            severity=AuditSeverity.INFO,
            timestamp=1234567890.0,
            user_id="user123",
            username="testuser",
            session_id=None,
            ip_address=None,
            user_agent=None,
            resource=None,
            action=None,
            details={},
            metadata={}
        )

        data = event.to_dict()

        assert data["event_id"] == "test_123"
        assert data["event_type"] == "user_login"
        assert data["severity"] == "info"
        assert data["user_id"] == "user123"
        assert "timestamp_iso" in data

    def test_audit_event_to_json(self):
        """Test converting audit event to JSON."""
        event = AuditEvent(
            event_id="test_123",
            event_type=AuditEventType.USER_LOGIN,
            severity=AuditSeverity.INFO,
            timestamp=1234567890.0,
            user_id="user123",
            username="testuser",
            session_id=None,
            ip_address=None,
            user_agent=None,
            resource=None,
            action=None,
            details={},
            metadata={}
        )

        json_str = event.to_json()
        data = json.loads(json_str)

        assert data["event_id"] == "test_123"
        assert data["event_type"] == "user_login"


class TestAuditLogger:
    """Test AuditLogger functionality."""

    def test_audit_logger_initialization(self):
        """Test audit logger initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            assert logger.log_file == log_file
            assert logger.max_file_size == 10 * 1024 * 1024
            assert logger.backup_count == 5

    def test_log_metadata_change(self):
        """Test logging metadata change."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            event_id = logger.log_metadata_change(
                user_id="user123",
                username="testuser",
                change_type="update",
                resource="kpi_definition",
                old_value="old_value",
                new_value="new_value"
            )

            assert event_id.startswith("meta_")

            # Check log file
            assert log_file.exists()
            content = log_file.read_text()
            assert "metadata_change" in content
            assert "user123" in content
            assert "kpi_definition" in content

    def test_log_query_execution(self):
        """Test logging query execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            event_id = logger.log_query_execution(
                user_id="user123",
                username="testuser",
                datasource="snowflake_main",
                sql="SELECT * FROM table",
                execution_time=1.5,
                row_count=100
            )

            assert event_id.startswith("query_")

            # Check log file
            content = log_file.read_text()
            assert "query_execution" in content
            assert "snowflake_main" in content
            assert "1.5" in content

    def test_log_user_login(self):
        """Test logging user login."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            event_id = logger.log_user_login(
                user_id="user123",
                username="testuser",
                success=True,
                ip_address="192.168.1.1"
            )

            assert event_id.startswith("login_")

            # Check log file
            content = log_file.read_text()
            assert "user_login" in content
            assert "user123" in content
            assert "192.168.1.1" in content

    def test_log_permission_denied(self):
        """Test logging permission denied."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            event_id = logger.log_permission_denied(
                user_id="user123",
                username="testuser",
                resource="admin_panel",
                action="access"
            )

            assert event_id.startswith("perm_")

            # Check log file
            content = log_file.read_text()
            assert "permission_denied" in content
            assert "admin_panel" in content
            assert "access" in content

    def test_log_system_error(self):
        """Test logging system error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            event_id = logger.log_system_error(
                error_type="DatabaseError",
                error_message="Connection failed",
                user_id="user123"
            )

            assert event_id.startswith("error_")

            # Check log file
            content = log_file.read_text()
            assert "system_error" in content
            assert "DatabaseError" in content
            assert "Connection failed" in content

    def test_get_recent_events(self):
        """Test getting recent events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            events = logger.get_recent_events()
            assert isinstance(events, list)

    def test_get_events_summary(self):
        """Test getting events summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            summary = logger.get_events_summary()
            assert isinstance(summary, dict)
            assert "total_events" in summary
            assert "events_by_type" in summary


class TestAuditLogAnalyzer:
    """Test audit log analyzer."""

    def test_analyze_user_activity(self):
        """Test user activity analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            audit_logger = AuditLogger(log_file=log_file, enable_console=False)
            analyzer = AuditLogAnalyzer(audit_logger)

            activity = analyzer.analyze_user_activity("user123")

            assert activity["user_id"] == "user123"
            assert "total_events" in activity
            assert "login_count" in activity

    def test_detect_anomalies(self):
        """Test anomaly detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            audit_logger = AuditLogger(log_file=log_file, enable_console=False)
            analyzer = AuditLogAnalyzer(audit_logger)

            anomalies = analyzer.detect_anomalies()

            assert isinstance(anomalies, list)

    def test_generate_compliance_report(self):
        """Test compliance report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            audit_logger = AuditLogger(log_file=log_file, enable_console=False)
            analyzer = AuditLogAnalyzer(audit_logger)

            report = analyzer.generate_compliance_report("2024-01-01", "2024-01-31")

            assert isinstance(report, dict)
            assert "report_period" in report
            assert "total_events" in report
            assert "compliance_score" in report


class TestAuditHelpers:
    """Test audit helper functions."""

    def test_audit_metadata_change(self):
        """Test metadata change audit helper."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            # Mock user
            user = MagicMock()
            user.user_id = "user123"
            user.username = "testuser"

            event_id = audit_metadata_change(
                logger, user, "update", "kpi_definition",
                old_value="old", new_value="new"
            )

            assert event_id.startswith("meta_")

            # Check log file
            content = log_file.read_text()
            assert "metadata_change" in content
            assert "user123" in content

    def test_audit_query_execution(self):
        """Test query execution audit helper."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            # Mock user
            user = MagicMock()
            user.user_id = "user123"
            user.username = "testuser"

            event_id = audit_query_execution(
                logger, user, "snowflake_main", "SELECT 1",
                execution_time=2.5, row_count=10
            )

            assert event_id.startswith("query_")

            # Check log file
            content = log_file.read_text()
            assert "query_execution" in content
            assert "snowflake_main" in content

    def test_audit_permission_denied(self):
        """Test permission denied audit helper."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            # Mock user
            user = MagicMock()
            user.user_id = "user123"
            user.username = "testuser"

            event_id = audit_permission_denied(
                logger, user, "admin_panel", "access"
            )

            assert event_id.startswith("perm_")

            # Check log file
            content = log_file.read_text()
            assert "permission_denied" in content
            assert "admin_panel" in content


class TestGlobalAuditLogger:
    """Test global audit logger functions."""

    def test_get_audit_logger(self):
        """Test getting global audit logger."""
        logger = get_audit_logger()
        assert isinstance(logger, AuditLogger)

    def test_init_audit_logger(self):
        """Test initializing global audit logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "custom_audit.log"
            logger = init_audit_logger(log_file=log_file)

            assert isinstance(logger, AuditLogger)
            assert logger.log_file == log_file

    def test_get_audit_logger_singleton(self):
        """Test that get_audit_logger returns singleton."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2


@pytest.mark.integration
class TestAuditIntegration:
    """Integration tests for audit logging."""

    def test_complete_audit_workflow(self):
        """Test complete audit logging workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "integration_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            # Log various events
            logger.log_user_login("user123", "testuser", True, ip_address="192.168.1.1")
            logger.log_query_execution("user123", "testuser", "snowflake_main", "SELECT 1", execution_time=1.0)
            logger.log_metadata_change("user123", "testuser", "update", "kpi_config")

            # Verify log file contains all events
            content = log_file.read_text()

            assert "user_login" in content
            assert "query_execution" in content
            assert "metadata_change" in content
            assert "user123" in content
            assert "192.168.1.1" in content

    def test_audit_event_persistence(self):
        """Test that audit events are persisted correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "persistence_audit.log"
            logger = AuditLogger(log_file=log_file, enable_console=False)

            # Log event
            event_id = logger.log_system_error("TestError", "Test message")

            # Wait for async logging
            time.sleep(0.1)

            # Verify file exists and contains data
            assert log_file.exists()
            content = log_file.read_text()

            assert event_id in content
            assert "system_error" in content
            assert "TestError" in content

    def test_audit_log_rotation(self):
        """Test log file rotation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "rotation_audit.log"
            logger = AuditLogger(
                log_file=log_file,
                max_file_size=100,  # Very small for testing
                backup_count=2,
                enable_console=False
            )

            # Log many events to trigger rotation
            for i in range(20):
                logger.log_user_login(f"user{i}", f"testuser{i}", True)

            # Wait for logging
            time.sleep(0.2)

            # Check for rotated files
            backup_files = list(log_file.parent.glob(f"{log_file.stem}*"))
            assert len(backup_files) > 1  # Should have original + backups