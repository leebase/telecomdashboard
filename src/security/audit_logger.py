"""Audit logging system for metadata runtime."""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from queue import Queue

import pandas as pd


class AuditEventType(Enum):
    """Types of audit events."""
    METADATA_CHANGE = "metadata_change"
    QUERY_EXECUTION = "query_execution"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_DENIED = "permission_denied"
    DATA_ACCESS = "data_access"
    CONFIG_CHANGE = "config_change"
    SYSTEM_ERROR = "system_error"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: float
    user_id: Optional[str]
    username: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource: Optional[str]
    action: Optional[str]
    details: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['timestamp_iso'] = datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """Central audit logging system."""

    def __init__(self,
                 log_file: Optional[Path] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 enable_console: bool = True):
        self.log_file = log_file or Path("logs/audit.log")
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_console = enable_console

        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Set up Python logging
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(file_handler)

        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(console_handler)

        # Async logging queue
        self.log_queue: Queue[AuditEvent] = Queue()
        self.worker_thread = threading.Thread(target=self._log_worker, daemon=True)
        self.worker_thread.start()

    def _log_worker(self):
        """Background worker for async logging."""
        while True:
            try:
                event = self.log_queue.get(timeout=1)
                self._write_event(event)
                self.log_queue.task_done()
            except:
                continue  # Continue processing even if one event fails

    def _write_event(self, event: AuditEvent):
        """Write audit event to log."""
        try:
            log_entry = event.to_json()
            self.logger.info(log_entry)
        except Exception as e:
            # Fallback logging if JSON serialization fails
            self.logger.error(f"Failed to serialize audit event {event.event_id}: {e}")

    def log_event(self, event: AuditEvent):
        """Log an audit event asynchronously."""
        self.log_queue.put(event)

    def log_metadata_change(self,
                           user_id: Optional[str],
                           username: Optional[str],
                           change_type: str,
                           resource: str,
                           old_value: Optional[Any] = None,
                           new_value: Optional[Any] = None,
                           session_id: Optional[str] = None,
                           ip_address: Optional[str] = None) -> str:
        """Log metadata change event."""
        event_id = f"meta_{int(time.time() * 1000000)}"

        details = {
            "change_type": change_type,
            "old_value": str(old_value) if old_value is not None else None,
            "new_value": str(new_value) if new_value is not None else None
        }

        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.METADATA_CHANGE,
            severity=AuditSeverity.INFO,
            timestamp=time.time(),
            user_id=user_id,
            username=username,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            resource=resource,
            action=change_type,
            details=details,
            metadata={}
        )

        self.log_event(event)
        return event_id

    def log_query_execution(self,
                           user_id: Optional[str],
                           username: Optional[str],
                           datasource: str,
                           sql: str,
                           params: Optional[Dict[str, Any]] = None,
                           execution_time: Optional[float] = None,
                           row_count: Optional[int] = None,
                           session_id: Optional[str] = None,
                           ip_address: Optional[str] = None) -> str:
        """Log query execution event."""
        event_id = f"query_{int(time.time() * 1000000)}"

        details = {
            "datasource": datasource,
            "sql_hash": hash(sql),  # Don't log actual SQL for security
            "execution_time": execution_time,
            "row_count": row_count,
            "has_params": params is not None
        }

        severity = AuditSeverity.INFO
        if execution_time and execution_time > 30:  # Slow query
            severity = AuditSeverity.WARNING
        elif execution_time and execution_time > 300:  # Very slow query
            severity = AuditSeverity.ERROR

        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.QUERY_EXECUTION,
            severity=severity,
            timestamp=time.time(),
            user_id=user_id,
            username=username,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            resource=datasource,
            action="execute_query",
            details=details,
            metadata={}
        )

        self.log_event(event)
        return event_id

    def log_user_login(self,
                      user_id: str,
                      username: str,
                      success: bool,
                      session_id: Optional[str] = None,
                      ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None) -> str:
        """Log user login event."""
        event_id = f"login_{int(time.time() * 1000000)}"

        details = {
            "success": success,
            "failure_reason": None if success else "invalid_credentials"
        }

        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING

        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.USER_LOGIN,
            severity=severity,
            timestamp=time.time(),
            user_id=user_id,
            username=username,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource="authentication",
            action="login",
            details=details,
            metadata={}
        )

        self.log_event(event)
        return event_id

    def log_permission_denied(self,
                             user_id: Optional[str],
                             username: Optional[str],
                             resource: str,
                             action: str,
                             session_id: Optional[str] = None,
                             ip_address: Optional[str] = None) -> str:
        """Log permission denied event."""
        event_id = f"perm_{int(time.time() * 1000000)}"

        details = {
            "requested_resource": resource,
            "requested_action": action
        }

        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.PERMISSION_DENIED,
            severity=AuditSeverity.WARNING,
            timestamp=time.time(),
            user_id=user_id,
            username=username,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            resource=resource,
            action=action,
            details=details,
            metadata={}
        )

        self.log_event(event)
        return event_id

    def log_system_error(self,
                        error_type: str,
                        error_message: str,
                        stack_trace: Optional[str] = None,
                        user_id: Optional[str] = None,
                        session_id: Optional[str] = None) -> str:
        """Log system error event."""
        event_id = f"error_{int(time.time() * 1000000)}"

        details = {
            "error_type": error_type,
            "error_message": error_message,
            "has_stack_trace": stack_trace is not None
        }

        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.SYSTEM_ERROR,
            severity=AuditSeverity.ERROR,
            timestamp=time.time(),
            user_id=user_id,
            username=None,
            session_id=session_id,
            ip_address=None,
            user_agent=None,
            resource="system",
            action="error",
            details=details,
            metadata={"stack_trace": stack_trace} if stack_trace else {}
        )

        self.log_event(event)
        return event_id

    def get_recent_events(self, limit: int = 100, event_type: Optional[AuditEventType] = None) -> List[AuditEvent]:
        """Get recent audit events (for monitoring/debugging)."""
        # In production, this would query from a database
        # For now, return empty list as we don't have persistent storage
        return []

    def get_events_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of audit events for the specified time period."""
        # In production, this would query audit logs
        return {
            "total_events": 0,
            "events_by_type": {},
            "events_by_severity": {},
            "top_users": [],
            "error_rate": 0.0
        }


class AuditLogAnalyzer:
    """Analyzer for audit log data."""

    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger

    def analyze_user_activity(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Analyze user activity patterns."""
        # In production, this would parse log files
        return {
            "user_id": user_id,
            "total_events": 0,
            "login_count": 0,
            "query_count": 0,
            "permission_denied_count": 0,
            "last_activity": None,
            "risk_score": 0.0
        }

    def detect_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Detect anomalous activity patterns."""
        # In production, this would analyze log patterns
        return []

    def generate_compliance_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate compliance report for specified date range."""
        # In production, this would parse logs and generate reports
        return {
            "report_period": f"{start_date} to {end_date}",
            "total_events": 0,
            "compliance_score": 100.0,
            "findings": [],
            "recommendations": []
        }


# Integration helpers
def audit_metadata_change(audit_logger: AuditLogger,
                         user: Optional[Any],
                         change_type: str,
                         resource: str,
                         old_value: Optional[Any] = None,
                         new_value: Optional[Any] = None) -> str:
    """Helper to audit metadata changes."""
    user_id = user.user_id if user else None
    username = user.username if user else None

    return audit_logger.log_metadata_change(
        user_id=user_id,
        username=username,
        change_type=change_type,
        resource=resource,
        old_value=old_value,
        new_value=new_value
    )


def audit_query_execution(audit_logger: AuditLogger,
                         user: Optional[Any],
                         datasource: str,
                         sql: str,
                         execution_time: Optional[float] = None,
                         row_count: Optional[int] = None) -> str:
    """Helper to audit query execution."""
    user_id = user.user_id if user else None
    username = user.username if user else None

    return audit_logger.log_query_execution(
        user_id=user_id,
        username=username,
        datasource=datasource,
        sql=sql,
        execution_time=execution_time,
        row_count=row_count
    )


def audit_permission_denied(audit_logger: AuditLogger,
                           user: Optional[Any],
                           resource: str,
                           action: str) -> str:
    """Helper to audit permission denied events."""
    user_id = user.user_id if user else None
    username = user.username if user else None

    return audit_logger.log_permission_denied(
        user_id=user_id,
        username=username,
        resource=resource,
        action=action
    )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None

def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

def init_audit_logger(log_file: Optional[Path] = None) -> AuditLogger:
    """Initialize global audit logger."""
    global _audit_logger
    _audit_logger = AuditLogger(log_file=log_file)
    return _audit_logger


__all__ = [
    "AuditEventType",
    "AuditSeverity",
    "AuditEvent",
    "AuditLogger",
    "AuditLogAnalyzer",
    "audit_metadata_change",
    "audit_query_execution",
    "audit_permission_denied",
    "get_audit_logger",
    "init_audit_logger"
]