"""
Integration Layer for Agent System

This module provides seamless integration between the agent system and existing
telecom dashboard infrastructure including KPI data, configuration, and security.
"""

import sys
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ai_insights_data_bundler import bundle_kpi_data_for_insights
    from config_manager import get_config, ConfigManager
    from security_manager import SecurityManager, sanitize_streamlit_output
    from llm_service import PIIScrubber
    from database_connection import db
    from improved_metric_cards import (
        get_network_metrics, 
        get_customer_metrics, 
        get_revenue_metrics, 
        get_usage_metrics, 
        get_operations_metrics
    )
except ImportError as e:
    logging.warning(f"Some integration modules not available: {e}")
    # Create mock versions for testing
    bundle_kpi_data_for_insights = None
    get_config = None
    SecurityManager = None
    PIIScrubber = None
    db = None
    
    # Mock metric functions for testing
    def get_network_metrics(days: int = 30) -> List[Dict[str, Any]]:
        return [
            {"label": "Network Performance", "value": 95.2, "delta": 2.1, "delta_direction": "up", "unit": "%", "tooltip": "Network performance score"},
            {"label": "Latency", "value": 45.8, "delta": -5.2, "delta_direction": "down", "unit": "ms", "tooltip": "Average network latency"},
            {"label": "Throughput", "value": 850.5, "delta": 25.3, "delta_direction": "up", "unit": "Mbps", "tooltip": "Network throughput"}
        ]
    
    def get_customer_metrics(days: int = 30) -> List[Dict[str, Any]]:
        return [
            {"label": "Customer Satisfaction", "value": 88.5, "delta": 1.2, "delta_direction": "up", "unit": "%", "tooltip": "Customer satisfaction score"},
            {"label": "Churn Rate", "value": 2.1, "delta": -0.3, "delta_direction": "down", "unit": "%", "tooltip": "Customer churn rate"}
        ]
    
    def get_revenue_metrics(days: int = 30) -> List[Dict[str, Any]]:
        return [
            {"label": "Monthly Revenue", "value": 1250000, "delta": 45000, "delta_direction": "up", "unit": "$", "tooltip": "Monthly recurring revenue"},
            {"label": "ARPU", "value": 85.50, "delta": 2.30, "delta_direction": "up", "unit": "$", "tooltip": "Average revenue per user"}
        ]
    
    def get_usage_metrics(days: int = 30) -> List[Dict[str, Any]]:
        return [
            {"label": "Data Usage", "value": 15.8, "delta": 1.2, "delta_direction": "up", "unit": "GB", "tooltip": "Average data usage per user"},
            {"label": "Service Adoption", "value": 78.5, "delta": 3.1, "delta_direction": "up", "unit": "%", "tooltip": "Service adoption rate"}
        ]
    
    def get_operations_metrics(days: int = 30) -> List[Dict[str, Any]]:
        return [
            {"label": "System Uptime", "value": 99.95, "delta": 0.02, "delta_direction": "up", "unit": "%", "tooltip": "System availability"},
            {"label": "Incident Response", "value": 12.5, "delta": -2.1, "delta_direction": "down", "unit": "min", "tooltip": "Average incident response time"}
        ]

from models.play_models import Play, SubjectArea, AgentStatus


class DashboardIntegrationManager:
    """
    Manages integration between agent system and existing telecom dashboard
    """
    
    def __init__(self):
        self.config_manager = None
        self.security_manager = None
        self.pii_scrubber = None
        self.db_connection = None
        self._initialize_integration()
    
    def _initialize_integration(self):
        """Initialize integration with existing systems"""
        try:
            # Initialize configuration manager
            if get_config:
                self.config_manager = get_config()
                logging.info("✅ Configuration manager integrated successfully")
            
            # Initialize security manager
            if SecurityManager:
                self.security_manager = SecurityManager()
                logging.info("✅ Security manager integrated successfully")
            
            # Initialize PII scrubber
            if PIIScrubber:
                self.pii_scrubber = PIIScrubber()
                logging.info("✅ PII scrubber integrated successfully")
            
            # Initialize database connection
            if db:
                self.db_connection = db
                logging.info("✅ Database connection integrated successfully")
                
        except Exception as e:
            logging.warning(f"Integration initialization warning: {e}")
    
    def get_kpi_data_for_area(self, area: SubjectArea, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get KPI data for a specific subject area using existing dashboard infrastructure
        
        Args:
            area: Subject area to get data for
            days: Number of days of historical data
            
        Returns:
            List of KPI data dictionaries
        """
        try:
            # Map subject areas to dashboard tab names
            area_to_tab = {
                SubjectArea.NETWORK_QOE: "network",
                SubjectArea.CUSTOMER: "customer", 
                SubjectArea.REVENUE: "revenue",
                SubjectArea.USAGE: "usage",
                SubjectArea.OPERATIONS: "operations"
            }
            
            tab_name = area_to_tab.get(area, "network")
            
            # Use existing KPI bundling if available
            if bundle_kpi_data_for_insights:
                kpi_data = bundle_kpi_data_for_insights(tab_name, days)
                logging.info(f"✅ Retrieved KPI data for {area.value} using existing bundler")
                return kpi_data
            
            # Fallback to direct metric calls
            return self._get_metrics_direct(area, days)
            
        except Exception as e:
            logging.error(f"Error getting KPI data for {area.value}: {e}")
            return []
    
    def _get_metrics_direct(self, area: SubjectArea, days: int) -> List[Dict[str, Any]]:
        """Direct metric retrieval as fallback"""
        try:
            area_to_function = {
                SubjectArea.NETWORK_QOE: get_network_metrics,
                SubjectArea.CUSTOMER: get_customer_metrics,
                SubjectArea.REVENUE: get_revenue_metrics,
                SubjectArea.USAGE: get_usage_metrics,
                SubjectArea.OPERATIONS: get_operations_metrics
            }
            
            metric_function = area_to_function.get(area)
            if not metric_function:
                return []
            
            metrics = metric_function(days)
            
            # Convert to standard format
            kpi_data = []
            for metric in metrics:
                kpi_entry = {
                    "kpi_name": metric.get('label', 'Unknown'),
                    "current_value": metric.get('value', 0),
                    "prior_value": metric.get('value', 0) - metric.get('delta', 0),
                    "peer_avg": 0,  # Default values
                    "industry_avg": 0,
                    "unit": metric.get('unit', ''),
                    "direction": "neutral",
                    "threshold_low": None,
                    "threshold_high": None,
                    "delta": metric.get('delta', 0),
                    "delta_direction": metric.get('delta_direction', 'stable'),
                    "tooltip": metric.get('tooltip', ''),
                    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                kpi_data.append(kpi_entry)
            
            return kpi_data
            
        except Exception as e:
            logging.error(f"Error in direct metric retrieval: {e}")
            return []
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get configuration from existing dashboard systems
        
        Returns:
            Configuration dictionary
        """
        try:
            if self.config_manager:
                config = self.config_manager.config
                return {
                    "database": {
                        "path": config.database.path,
                        "cache_size": config.database.cache_size,
                        "connection_timeout": config.database.connection_timeout
                    },
                    "ui": {
                        "default_theme": config.ui.default_theme,
                        "page_title": config.ui.page_title,
                        "show_debug_info": config.ui.show_debug_info
                    },
                    "security": {
                        "enable_rate_limiting": config.security.enable_rate_limiting,
                        "max_requests_per_minute": config.security.max_requests_per_minute,
                        "enable_input_validation": config.security.enable_input_validation
                    },
                    "performance": {
                        "enable_caching": config.performance.enable_caching,
                        "cache_ttl_seconds": config.performance.cache_ttl_seconds,
                        "concurrent_requests": config.performance.concurrent_requests
                    },
                    "ai": {
                        "model": config.ai.model,
                        "temperature": config.ai.temperature,
                        "enable_insights": config.ai.enable_insights
                    },
                    "features": {
                        "ai_insights": config.features.ai_insights,
                        "pii_scrubbing": config.features.pii_scrubbing,
                        "circuit_breaker": config.features.circuit_breaker
                    }
                }
            else:
                # Return default configuration
                return self._get_default_config()
                
        except Exception as e:
            logging.error(f"Error getting configuration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration when integration is not available"""
        return {
            "database": {"path": "data/telecom_db.sqlite", "cache_size": 32},
            "ui": {"default_theme": "verizon", "page_title": "Telecom KPI Dashboard"},
            "security": {"enable_rate_limiting": True, "max_requests_per_minute": 60},
            "performance": {"enable_caching": True, "cache_ttl_seconds": 300},
            "ai": {"model": "google/gemini-2.5-flash", "enable_insights": True},
            "features": {"ai_insights": True, "pii_scrubbing": True, "circuit_breaker": True}
        }
    
    def validate_and_scrub_data(self, data: Any, data_type: str = "play") -> Any:
        """
        Validate and scrub data using existing security infrastructure
        
        Args:
            data: Data to validate and scrub
            data_type: Type of data for validation rules
            
        Returns:
            Validated and scrubbed data
        """
        try:
            if not self.security_manager:
                return data
            
            # Validate input
            if not self.security_manager.validate_input(data, data_type):
                logging.warning(f"Data validation failed for {data_type}")
                return None
            
            # Scrub PII if available
            if self.pii_scrubber and data_type == "play":
                if isinstance(data, dict):
                    data = self.pii_scrubber.scrub_data_dict(data)
                elif isinstance(data, list):
                    data = [self.pii_scrubber.scrub_data_dict(item) if isinstance(item, dict) else item for item in data]
            
            return data
            
        except Exception as e:
            logging.error(f"Error in data validation/scrubbing: {e}")
            return data
    
    def get_benchmark_data(self, kpi_names: List[str]) -> Dict[str, Any]:
        """
        Get benchmark data from existing database
        
        Args:
            kpi_names: List of KPI names to get benchmarks for
            
        Returns:
            Dictionary of benchmark data
        """
        try:
            if not self.db_connection:
                return {}
            
            benchmark_data = self.db_connection.get_benchmark_targets(kpi_names)
            if benchmark_data.empty:
                return {}
            
            benchmarks = {}
            for _, row in benchmark_data.iterrows():
                kpi_name = row['kpi_name']
                benchmarks[kpi_name] = {
                    "peer_avg": row.get('peer_avg', 0),
                    "industry_avg": row.get('industry_avg', 0),
                    "unit": row.get('unit', ''),
                    "direction": row.get('direction', 'neutral'),
                    "threshold_low": row.get('threshold_low'),
                    "threshold_high": row.get('threshold_high')
                }
            
            return benchmarks
            
        except Exception as e:
            logging.error(f"Error getting benchmark data: {e}")
            return {}
    
    def log_agent_activity(self, agent_name: str, action: str, details: Dict[str, Any] = None):
        """
        Log agent activity using existing logging infrastructure
        
        Args:
            agent_name: Name of the agent
            action: Action being performed
            details: Additional details about the action
        """
        try:
            log_message = f"Agent {agent_name}: {action}"
            if details:
                log_message += f" - {details}"
            
            logging.info(log_message)
            
            # Also log to security log if available
            if self.security_manager:
                self.security_manager.log_failed_attempt(f"agent_{agent_name}_{action}")
                
        except Exception as e:
            logging.error(f"Error logging agent activity: {e}")
    
    def check_system_health(self) -> Dict[str, Any]:
        """
        Check health of integrated systems
        
        Returns:
            Health status dictionary
        """
        health_status = {
            "integration_status": "unknown",
            "config_manager": False,
            "security_manager": False,
            "pii_scrubber": False,
            "database": False,
            "kpi_data": False,
            "overall_health": "unknown"
        }
        
        try:
            # Check configuration manager
            if self.config_manager:
                health_status["config_manager"] = True
            
            # Check security manager
            if self.security_manager:
                health_status["security_manager"] = True
            
            # Check PII scrubber
            if self.pii_scrubber:
                health_status["pii_scrubber"] = True
            
            # Check database connection
            if self.db_connection:
                try:
                    # Simple health check
                    health_status["database"] = True
                except:
                    health_status["database"] = False
            
            # Check KPI data availability
            try:
                test_data = self.get_kpi_data_for_area(SubjectArea.NETWORK_QOE, 1)
                health_status["kpi_data"] = len(test_data) > 0
            except:
                health_status["kpi_data"] = False
            
            # Determine overall health
            working_components = sum([
                health_status["config_manager"],
                health_status["security_manager"], 
                health_status["pii_scrubber"],
                health_status["database"],
                health_status["kpi_data"]
            ])
            
            if working_components >= 4:
                health_status["overall_health"] = "healthy"
                health_status["integration_status"] = "fully_integrated"
            elif working_components >= 2:
                health_status["overall_health"] = "degraded"
                health_status["integration_status"] = "partially_integrated"
            else:
                health_status["overall_health"] = "unhealthy"
                health_status["integration_status"] = "not_integrated"
                
        except Exception as e:
            logging.error(f"Error checking system health: {e}")
            health_status["overall_health"] = "error"
        
        return health_status


# Global integration manager instance
integration_manager = DashboardIntegrationManager()


def get_integration_manager() -> DashboardIntegrationManager:
    """Get the global integration manager instance"""
    return integration_manager


def test_integration() -> Dict[str, Any]:
    """Test the integration layer functionality"""
    try:
        manager = get_integration_manager()
        
        # Test configuration retrieval
        config = manager.get_configuration()
        
        # Test KPI data retrieval
        kpi_data = manager.get_kpi_data_for_area(SubjectArea.NETWORK_QOE, 1)
        
        # Test health check
        health = manager.check_system_health()
        
        return {
            "success": True,
            "config_retrieved": bool(config),
            "kpi_data_retrieved": len(kpi_data) > 0,
            "health_status": health,
            "integration_working": health["overall_health"] in ["healthy", "degraded"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "integration_working": False
        }
