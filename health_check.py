"""
Health Check and Feature Flag System for Enterprise Deployment

This module provides health check endpoints and feature flag management
for production monitoring and safe feature rollouts.
"""

import time
import psutil
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from database_connection import TelecomDatabase
from config_manager import get_config
from logging_config import get_logger

logger = get_logger('health_check')

# Import version information
from __version__ import APP_VERSION

@dataclass
class HealthCheckResult:
    """Result of a health check operation"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    details: Dict[str, Any]
    timestamp: str

class FeatureFlags:
    """
    Simple feature flag system for safe rollouts
    
    Supports environment-based feature toggles and gradual rollouts
    """
    
    def __init__(self):
        """Initialize feature flag system"""
        config = get_config()
        features = getattr(config, "features", None)

        if features is not None:
            self.flags = {
                # Canonical names from FeatureConfig
                "ai_insights": features.ai_insights,
                "ai_insights_beta": features.ai_insights_beta,
                "pii_scrubbing": features.pii_scrubbing,
                "cache_ttl": features.cache_ttl,
                "circuit_breaker": features.circuit_breaker,
                "connection_pooling": features.connection_pooling,
                "structured_logging": features.structured_logging,
                "snowflake_query_tagging": features.snowflake_query_tagging,
                "health_checks_detailed": features.health_checks_detailed,
                "theme_switching": features.theme_switching,
                "benchmark_management": features.benchmark_management,
                "print_mode": features.print_mode,
                "security_headers": features.security_headers,
                "rate_limiting": features.rate_limiting,
                "sql_injection_protection": features.sql_injection_protection,

                # Compatibility aliases for older callers
                "ai_insights_enabled": features.ai_insights,
                "pii_scrubbing_enabled": features.pii_scrubbing,
                "cache_ttl_enabled": features.cache_ttl,
                "circuit_breaker_enabled": features.circuit_breaker,
                "connection_pooling_enabled": features.connection_pooling,
                "theme_switching_enabled": features.theme_switching,
                "print_mode_enabled": features.print_mode,
                "security_headers_enabled": features.security_headers,
                "rate_limiting_enabled": features.rate_limiting,
            }
        else:
            self.flags = {
                "ai_insights_enabled": True,
                "ai_insights_beta": False,
                "pii_scrubbing_enabled": True,
                "cache_ttl_enabled": True,
                "circuit_breaker_enabled": True,
                "connection_pooling_enabled": True,
                "structured_logging": False,
                "snowflake_query_tagging": True,
                "health_checks_detailed": True,
                "theme_switching_enabled": True,
                "benchmark_management": True,
                "print_mode_enabled": True,
                "security_headers_enabled": True,
                "rate_limiting_enabled": True,
                "sql_injection_protection": True,
            }
        
        # Load environment overrides
        self._load_environment_overrides()
    
    def _load_environment_overrides(self):
        """Load feature flag overrides from environment variables"""
        import os
        
        for flag_name in self.flags.keys():
            env_var = f"FEATURE_{flag_name.upper()}"
            env_value = os.getenv(env_var)
            
            if env_value is not None:
                # Convert string to boolean
                if env_value.lower() in ('true', '1', 'yes', 'on'):
                    self.flags[flag_name] = True
                elif env_value.lower() in ('false', '0', 'no', 'off'):
                    self.flags[flag_name] = False
                
                logger.info(f"Feature flag override: {flag_name} = {self.flags[flag_name]} (from {env_var})")
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self.flags.get(flag_name, False)
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags and their status"""
        return self.flags.copy()
    
    def set_flag(self, flag_name: str, enabled: bool):
        """Set a feature flag (for testing/admin use)"""
        self.flags[flag_name] = enabled
        logger.info(f"Feature flag updated: {flag_name} = {enabled}")

class HealthChecker:
    """
    Comprehensive health check system for production monitoring
    
    Checks database, dependencies, system resources, and feature availability
    """
    
    def __init__(self):
        """Initialize health checker"""
        self.feature_flags = FeatureFlags()
    
    def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            db = TelecomDatabase()
            
            # Test basic connectivity
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    response_time = (time.time() - start_time) * 1000
                    return HealthCheckResult(
                        name="database",
                        status="healthy",
                        response_time_ms=response_time,
                        details={
                            "connection_type": "sqlite",
                            "test_query": "SELECT 1",
                            "database_file": str(db.db_path)
                        },
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                else:
                    return HealthCheckResult(
                        name="database",
                        status="unhealthy",
                        response_time_ms=(time.time() - start_time) * 1000,
                        details={"error": "Test query failed"},
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def check_system_resources(self) -> HealthCheckResult:
        """Check system resource utilization"""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine health status based on thresholds
            status = "healthy"
            warnings = []
            
            if cpu_percent > 80:
                status = "degraded"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            elif cpu_percent > 90:
                status = "unhealthy"
                warnings.append(f"Critical CPU usage: {cpu_percent}%")
            
            if memory.percent > 80:
                status = "degraded"
                warnings.append(f"High memory usage: {memory.percent}%")
            elif memory.percent > 90:
                status = "unhealthy"
                warnings.append(f"Critical memory usage: {memory.percent}%")
            
            if disk.percent > 80:
                status = "degraded"
                warnings.append(f"High disk usage: {disk.percent}%")
            elif disk.percent > 90:
                status = "unhealthy"
                warnings.append(f"Critical disk usage: {disk.percent}%")
            
            return HealthCheckResult(
                name="system_resources",
                status=status,
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                    "warnings": warnings
                },
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="system_resources",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def check_ai_service(self) -> HealthCheckResult:
        """Check AI service availability"""
        start_time = time.time()
        
        try:
            if not self.feature_flags.is_enabled("ai_insights_enabled"):
                return HealthCheckResult(
                    name="ai_service",
                    status="healthy",
                    response_time_ms=(time.time() - start_time) * 1000,
                    details={"status": "disabled_by_feature_flag"},
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            
            from llm_service import LLMService
            
            # Test basic LLM service initialization
            llm = LLMService()
            
            # Check if API key is configured
            if not llm.config.get('api_key'):
                return HealthCheckResult(
                    name="ai_service",
                    status="degraded",
                    response_time_ms=(time.time() - start_time) * 1000,
                    details={"error": "API key not configured"},
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            
            return HealthCheckResult(
                name="ai_service",
                status="healthy",
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    "provider": llm.config.get('provider', 'unknown'),
                    "model": llm.config.get('model', 'unknown'),
                    "circuit_breaker_state": llm.circuit_breaker.state.value,
                    "pii_scrubbing_enabled": self.feature_flags.is_enabled("pii_scrubbing_enabled")
                },
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="ai_service",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def check_file_permissions(self) -> HealthCheckResult:
        """Check critical file permissions and accessibility"""
        start_time = time.time()
        
        try:
            critical_paths = [
                "logs/",
                "config/",
                "data/",
                "config/pii_config.yaml"
            ]
            
            issues = []
            
            import os
            
            for path_str in critical_paths:
                path = Path(path_str)
                
                if not path.exists():
                    issues.append(f"Missing: {path}")
                    continue
                
                if path.is_dir():
                    if not path.is_dir() or not os.access(path, os.W_OK):
                        issues.append(f"Directory not writable: {path}")
                else:
                    if not os.access(path, os.R_OK):
                        issues.append(f"File not readable: {path}")
            
            status = "unhealthy" if issues else "healthy"
            
            return HealthCheckResult(
                name="file_permissions",
                status=status,
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    "checked_paths": critical_paths,
                    "issues": issues
                },
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="file_permissions",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health check results"""
        checks = [
            self.check_database_health(),
            self.check_system_resources(),
            self.check_ai_service(),
            self.check_file_permissions()
        ]
        
        # Overall status determination
        statuses = [check.status for check in checks]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {check.name: {
                "status": check.status,
                "response_time_ms": check.response_time_ms,
                "details": check.details,
                "timestamp": check.timestamp
            } for check in checks},
            "feature_flags": self.feature_flags.get_all_flags(),
            "version": APP_VERSION,
            "environment": __import__('os').getenv("ENVIRONMENT", "development")
        }

    def run_all_checks(self) -> Dict[str, Any]:
        """Compatibility wrapper for callers expecting a single aggregate runner."""
        return self.get_comprehensive_health()
    
    def get_simple_health(self) -> Dict[str, str]:
        """Get simple health check for load balancers"""
        try:
            # Quick database connectivity check
            db = TelecomDatabase()
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": APP_VERSION
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": APP_VERSION
            }

# Global instances
feature_flags = FeatureFlags()
health_checker = HealthChecker()
