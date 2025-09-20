"""Production monitoring and health check system for metadata runtime."""

from __future__ import annotations

import os
import psutil
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

import pandas as pd


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentStatus(Enum):
    """Component status levels."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component: str
    status: ComponentStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "response_time": self.response_time
        }


@dataclass
class SystemMetrics:
    """System performance metrics."""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_connections: int
    thread_count: int
    open_files: int
    uptime_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_usage_percent": self.disk_usage_percent,
            "network_connections": self.network_connections,
            "thread_count": self.thread_count,
            "open_files": self.open_files,
            "uptime_seconds": self.uptime_seconds
        }


class HealthChecker:
    """Central health check system."""

    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}
        self.alert_callbacks: List[Callable[[HealthCheckResult], None]] = []
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = False

    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """Register a health check function."""
        self.checks[name] = check_func

    def unregister_check(self, name: str):
        """Unregister a health check."""
        self.checks.pop(name, None)
        self.last_results.pop(name, None)

    def add_alert_callback(self, callback: Callable[[HealthCheckResult], None]):
        """Add callback for health check alerts."""
        self.alert_callbacks.append(callback)

    def run_check(self, name: str) -> Optional[HealthCheckResult]:
        """Run a specific health check."""
        if name not in self.checks:
            return None

        start_time = time.time()
        try:
            result = self.checks[name]()
            result.response_time = time.time() - start_time
            result.timestamp = datetime.now()

            self.last_results[name] = result

            # Trigger alerts for non-healthy status
            if result.status in [ComponentStatus.WARNING, ComponentStatus.ERROR]:
                for callback in self.alert_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        print(f"Alert callback error: {e}")

            return result

        except Exception as e:
            error_result = HealthCheckResult(
                component=name,
                status=ComponentStatus.ERROR,
                message=f"Health check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
            self.last_results[name] = error_result
            return error_result

    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        for name in self.checks:
            result = self.run_check(name)
            if result:
                results[name] = result
        return results

    def get_overall_health(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.last_results:
            return HealthStatus.UNHEALTHY

        statuses = [result.status for result in self.last_results.values()]

        if any(status == ComponentStatus.ERROR for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == ComponentStatus.WARNING for status in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        overall_status = self.get_overall_health()
        results = self.run_all_checks()

        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
            "total_checks": len(results),
            "healthy_checks": sum(1 for r in results.values() if r.status == ComponentStatus.OK),
            "warning_checks": sum(1 for r in results.values() if r.status == ComponentStatus.WARNING),
            "error_checks": sum(1 for r in results.values() if r.status == ComponentStatus.ERROR)
        }

    def start_monitoring(self):
        """Start background monitoring."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return

        self._stop_monitoring = False
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()

    def stop_monitoring(self):
        """Stop background monitoring."""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)

    def _monitoring_loop(self):
        """Background monitoring loop."""
        while not self._stop_monitoring:
            try:
                self.run_all_checks()
            except Exception as e:
                print(f"Monitoring error: {e}")
            time.sleep(self.check_interval)


class MetricsCollector:
    """System and application metrics collector."""

    def __init__(self):
        self.start_time = time.time()
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 100

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_connections()
            threads = threading.active_count()

            # Get open files count (approximate)
            try:
                open_files = len(psutil.Process().open_files())
            except:
                open_files = 0

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                network_connections=len(network),
                thread_count=threads,
                open_files=open_files,
                uptime_seconds=time.time() - self.start_time
            )

            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)

            return metrics

        except Exception as e:
            # Return default metrics on error
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_usage_percent=0.0,
                network_connections=0,
                thread_count=1,
                open_files=0,
                uptime_seconds=time.time() - self.start_time
            )

    def get_metrics_history(self, limit: int = 10) -> List[SystemMetrics]:
        """Get recent metrics history."""
        return self.metrics_history[-limit:] if self.metrics_history else []

    def get_average_metrics(self, minutes: int = 5) -> Optional[SystemMetrics]:
        """Get average metrics over specified time period."""
        if not self.metrics_history:
            return None

        # Calculate how many recent metrics to average
        interval_seconds = minutes * 60
        recent_metrics = []
        cutoff_time = time.time() - interval_seconds

        for metric in reversed(self.metrics_history):
            if time.time() - (self.start_time + metric.uptime_seconds) > interval_seconds:
                break
            recent_metrics.append(metric)

        if not recent_metrics:
            return None

        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk = sum(m.disk_usage_percent for m in recent_metrics) / len(recent_metrics)
        avg_network = sum(m.network_connections for m in recent_metrics) / len(recent_metrics)
        avg_threads = sum(m.thread_count for m in recent_metrics) / len(recent_metrics)
        avg_files = sum(m.open_files for m in recent_metrics) / len(recent_metrics)

        return SystemMetrics(
            cpu_percent=avg_cpu,
            memory_percent=avg_memory,
            disk_usage_percent=avg_disk,
            network_connections=int(avg_network),
            thread_count=int(avg_threads),
            open_files=int(avg_files),
            uptime_seconds=sum(m.uptime_seconds for m in recent_metrics) / len(recent_metrics)
        )


class AlertManager:
    """Alert management system."""

    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self.alert_handlers: List[Callable[[Dict[str, Any]], None]] = []

    def add_alert_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Add alert handler function."""
        self.alert_handlers.append(handler)

    def trigger_alert(self, alert_type: str, severity: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Trigger an alert."""
        alert = {
            "id": f"alert_{int(time.time() * 1000000)}",
            "type": alert_type,
            "severity": severity,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "acknowledged": False
        }

        self.alerts.append(alert)

        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Alert handler error: {e}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active (unacknowledged) alerts."""
        return [alert for alert in self.alerts if not alert["acknowledged"]]

    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                break

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        active_alerts = self.get_active_alerts()
        total_alerts = len(self.alerts)

        severity_counts = {}
        type_counts = {}

        for alert in self.alerts:
            severity_counts[alert["severity"]] = severity_counts.get(alert["severity"], 0) + 1
            type_counts[alert["type"]] = type_counts.get(alert["type"], 0) + 1

        return {
            "total_alerts": total_alerts,
            "active_alerts": len(active_alerts),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "most_recent": self.alerts[-1] if self.alerts else None
        }


# Built-in health checks
def create_database_health_check(db_path: str) -> Callable[[], HealthCheckResult]:
    """Create database connectivity health check."""
    def check() -> HealthCheckResult:
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()

            return HealthCheckResult(
                component="database",
                status=ComponentStatus.OK,
                message="Database connection successful",
                details={"db_path": db_path},
                timestamp=datetime.now(),
                response_time=0.0
            )
        except Exception as e:
            return HealthCheckResult(
                component="database",
                status=ComponentStatus.ERROR,
                message=f"Database connection failed: {e}",
                details={"db_path": db_path, "error": str(e)},
                timestamp=datetime.now(),
                response_time=0.0
            )
    return check


def create_filesystem_health_check(threshold_percent: float = 90.0) -> Callable[[], HealthCheckResult]:
    """Create filesystem usage health check."""
    def check() -> HealthCheckResult:
        try:
            disk = psutil.disk_usage('/')
            usage_percent = disk.percent

            if usage_percent >= threshold_percent:
                status = ComponentStatus.ERROR
                message = f"Disk usage critical: {usage_percent:.1f}%"
            elif usage_percent >= threshold_percent * 0.8:
                status = ComponentStatus.WARNING
                message = f"Disk usage high: {usage_percent:.1f}%"
            else:
                status = ComponentStatus.OK
                message = f"Disk usage normal: {usage_percent:.1f}%"

            return HealthCheckResult(
                component="filesystem",
                status=status,
                message=message,
                details={
                    "usage_percent": usage_percent,
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3)
                },
                timestamp=datetime.now(),
                response_time=0.0
            )
        except Exception as e:
            return HealthCheckResult(
                component="filesystem",
                status=ComponentStatus.ERROR,
                message=f"Filesystem check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time=0.0
            )
    return check


def create_memory_health_check(threshold_percent: float = 85.0) -> Callable[[], HealthCheckResult]:
    """Create memory usage health check."""
    def check() -> HealthCheckResult:
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent

            if usage_percent >= threshold_percent:
                status = ComponentStatus.ERROR
                message = f"Memory usage critical: {usage_percent:.1f}%"
            elif usage_percent >= threshold_percent * 0.8:
                status = ComponentStatus.WARNING
                message = f"Memory usage high: {usage_percent:.1f}%"
            else:
                status = ComponentStatus.OK
                message = f"Memory usage normal: {usage_percent:.1f}%"

            return HealthCheckResult(
                component="memory",
                status=status,
                message=message,
                details={
                    "usage_percent": usage_percent,
                    "total_gb": memory.total / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "available_gb": memory.available / (1024**3)
                },
                timestamp=datetime.now(),
                response_time=0.0
            )
        except Exception as e:
            return HealthCheckResult(
                component="memory",
                status=ComponentStatus.ERROR,
                message=f"Memory check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time=0.0
            )
    return check


# Global instances
health_checker = HealthChecker()
metrics_collector = MetricsCollector()
alert_manager = AlertManager()

# Initialize with default checks
health_checker.register_check("database", create_database_health_check("data/telecom_db.sqlite"))
health_checker.register_check("filesystem", create_filesystem_health_check())
health_checker.register_check("memory", create_memory_health_check())

# Default alert handler (logs to console)
def default_alert_handler(alert: Dict[str, Any]):
    """Default alert handler that logs alerts."""
    severity = alert.get("severity", "info").upper()
    message = alert.get("message", "Unknown alert")
    print(f"[{severity}] ALERT: {message}")

alert_manager.add_alert_handler(default_alert_handler)

# Health check alert integration
def health_check_alert_handler(result: HealthCheckResult):
    """Handle health check results and trigger alerts."""
    if result.status == ComponentStatus.ERROR:
        alert_manager.trigger_alert(
            alert_type="health_check",
            severity="critical",
            message=f"Health check failed: {result.component}",
            details=result.to_dict()
        )
    elif result.status == ComponentStatus.WARNING:
        alert_manager.trigger_alert(
            alert_type="health_check",
            severity="warning",
            message=f"Health check warning: {result.component}",
            details=result.to_dict()
        )

health_checker.add_alert_callback(health_check_alert_handler)


__all__ = [
    "HealthStatus",
    "ComponentStatus",
    "HealthCheckResult",
    "SystemMetrics",
    "HealthChecker",
    "MetricsCollector",
    "AlertManager",
    "create_database_health_check",
    "create_filesystem_health_check",
    "create_memory_health_check",
    "health_checker",
    "metrics_collector",
    "alert_manager"
]