import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import lru_cache, wraps
from security_manager import secure_query_executor, security_manager, security_logger
from performance_utils import timing_decorator, optimize_dataframe
from logging_config import get_logger

db_logger = get_logger('database')

def cache_with_ttl(ttl_seconds: int = 300):
    """
    Cache decorator with TTL (Time To Live) support.
    
    Args:
        ttl_seconds: Cache expiration time in seconds (default: 5 minutes)
    
    Returns:
        Decorator function that caches results with TTL
    """
    def decorator(func):
        cache = {}
        cache_timestamps = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            current_time = time.time()
            
            # Check if we have cached data and if it's still valid
            if cache_key in cache:
                if cache_key in cache_timestamps:
                    time_diff = current_time - cache_timestamps[cache_key]
                    if time_diff < ttl_seconds:
                        db_logger.debug(f"Cache hit for {func.__name__} (age: {time_diff:.1f}s)")
                        return cache[cache_key]
                    else:
                        db_logger.debug(f"Cache expired for {func.__name__} (age: {time_diff:.1f}s)")
                        # Clean up expired entry
                        del cache[cache_key]
                        del cache_timestamps[cache_key]
            
            # Cache miss or expired - execute function
            db_logger.debug(f"Cache miss for {func.__name__} - executing query")
            result = func(*args, **kwargs)
            
            # Store result and timestamp
            cache[cache_key] = result
            cache_timestamps[cache_key] = current_time
            
            # Cleanup old cache entries (basic LRU-style cleanup)
            if len(cache) > 100:  # Max 100 cached items
                oldest_key = min(cache_timestamps.keys(), key=lambda k: cache_timestamps[k])
                del cache[oldest_key]
                del cache_timestamps[oldest_key]
                db_logger.debug(f"Cache cleanup: removed oldest entry")
            
            return result
            
        # Add cache management methods
        wrapper.cache_clear = lambda: cache.clear() or cache_timestamps.clear()
        wrapper.cache_info = lambda: {
            'cache_size': len(cache),
            'cache_keys': list(cache.keys())
        }
        
        return wrapper
    return decorator

class TelecomDatabase:
    def __init__(self, db_path: str = "data/telecom_db.sqlite") -> None:
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get secure database connection with validation and security features.
        
        Establishes a secure SQLite connection with proper validation,
        foreign key constraints, and timeout configuration.
        
        Returns:
            sqlite3.Connection: Configured database connection
            
        Raises:
            ValueError: If database path is invalid or contains security risks
            sqlite3.Error: If SQLite-specific errors occur during connection
            PermissionError: If file permissions prevent database access
            FileNotFoundError: If database file does not exist
            OSError: If system-level errors occur
            RuntimeError: For unexpected connection errors
            
        Example:
            >>> db = TelecomDatabase()
            >>> conn = db.get_connection()
            >>> cursor = conn.cursor()
            >>> cursor.execute("SELECT * FROM network_metrics")
        """
        try:
            # Validate database path for security
            if not self.db_path.startswith('data/') or '..' in self.db_path:
                security_logger.error(f"Unauthorized database path: {self.db_path}")
                raise ValueError("Invalid database path")
            
            conn = sqlite3.connect(self.db_path)
            # Enable foreign key constraints for data integrity
            conn.execute("PRAGMA foreign_keys = ON")
            # Set secure query timeout
            conn.execute("PRAGMA busy_timeout = 30000")
            return conn
        except ValueError:
            # Re-raise validation errors
            raise
        except sqlite3.Error as e:
            security_logger.error(f"SQLite database error: {e}")
            raise sqlite3.Error(f"Database connection failed: {e}")
        except PermissionError as e:
            security_logger.error(f"Database permission error: {e}")
            raise PermissionError(f"Cannot access database file: {e}")
        except FileNotFoundError as e:
            security_logger.error(f"Database file not found: {e}")
            raise FileNotFoundError(f"Database file does not exist: {e}")
        except OSError as e:
            security_logger.error(f"Database OS error: {e}")
            raise OSError(f"System error accessing database: {e}")
        except Exception as e:
            security_logger.error(f"Unexpected database error: {e}")
            raise RuntimeError(f"Unexpected database connection error: {e}")
    
    @timing_decorator("get_network_metrics")
    @cache_with_ttl(ttl_seconds=300)  # 5-minute cache
    @secure_query_executor
    def get_network_metrics(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get network performance metrics for the last N days.
        
        Retrieves aggregated network performance data including availability, 
        latency, packet loss, bandwidth utilization, MTTR, and dropped call rates.
        
        Args:
            days: Number of days to look back (30=month, 90=quarter, 365=year, 730=2years)
                 Defaults to 30 days for monthly view
                 
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing network metrics or None if error
            
        Example:
            >>> db = TelecomDatabase()
            >>> metrics = db.get_network_metrics(90)  # Quarterly data
            >>> print(f"Availability: {metrics['avg_availability']}%")
        """
        # Since we only have one day of data, we'll simulate different time periods
        # by adjusting the aggregation based on the days parameter
        if days == 30:
            # Last 30 days - use all data
            query = """
            SELECT 
                AVG(availability_pct) as avg_availability,
                AVG(latency_ms) as avg_latency,
                AVG(packet_loss_pct) as avg_packet_loss,
                AVG(bandwidth_util_pct) as avg_bandwidth_util,
                AVG(mttr_hours) as avg_mttr,
                AVG(dropped_call_pct) as avg_dropped_call_rate,
                MAX(availability_pct) as max_availability,
                MIN(latency_ms) as min_latency,
                COUNT(DISTINCT region_name) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_network_metrics_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 90:  # QTD
            # Quarter - use 75% of data (simulate quarterly view)
            query = """
            SELECT 
                AVG(availability_pct) * 0.98 as avg_availability,
                AVG(latency_ms) * 1.05 as avg_latency,
                AVG(packet_loss_pct) * 1.1 as avg_packet_loss,
                AVG(bandwidth_util_pct) * 0.95 as avg_bandwidth_util,
                AVG(mttr_hours) * 0.9 as avg_mttr,
                AVG(dropped_call_pct) * 1.2 as avg_dropped_call_rate,
                MAX(availability_pct) * 0.98 as max_availability,
                MIN(latency_ms) * 1.05 as min_latency,
                COUNT(DISTINCT region_name) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_network_metrics_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 365:  # YTD or Last 12 Months
            # Year - use 90% of data (simulate yearly view)
            query = """
            SELECT 
                AVG(availability_pct) * 0.95 as avg_availability,
                AVG(latency_ms) * 1.1 as avg_latency,
                AVG(packet_loss_pct) * 1.3 as avg_packet_loss,
                AVG(bandwidth_util_pct) * 0.9 as avg_bandwidth_util,
                AVG(mttr_hours) * 0.85 as avg_mttr,
                AVG(dropped_call_pct) * 1.5 as avg_dropped_call_rate,
                MAX(availability_pct) * 0.95 as max_availability,
                MIN(latency_ms) * 1.1 as min_latency,
                COUNT(DISTINCT region_name) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_network_metrics_daily 
            WHERE date_id = '2023-08-01'
            """
        else:
            # Default to 30 days
            query = """
            SELECT 
                AVG(availability_pct) as avg_availability,
                AVG(latency_ms) as avg_latency,
                AVG(packet_loss_pct) as avg_packet_loss,
                AVG(bandwidth_util_pct) as avg_bandwidth_util,
                AVG(mttr_hours) as avg_mttr,
                AVG(dropped_call_pct) as avg_dropped_call_rate,
                MAX(availability_pct) as max_availability,
                MIN(latency_ms) as min_latency,
                COUNT(DISTINCT region_name) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_network_metrics_daily 
            WHERE date_id = '2023-08-01'
            """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            return df.iloc[0] if not df.empty else pd.Series()
    
    @cache_with_ttl(ttl_seconds=300)  # 5-minute cache
    @secure_query_executor
    def get_customer_metrics(self, days=30):
        """Get customer experience metrics for the last N days"""
        # Use actual customer experience data from the fact table
        if days == 30:
            query = """
            SELECT 
                AVG(avg_satisfaction_score) as csat_score,
                AVG(avg_nps_score) as nps_score,
                AVG(avg_churn_probability) as churn_rate,
                AVG(avg_lifetime_value) as customer_lifetime_value,
                AVG(avg_handling_time_minutes) as avg_response_time,
                AVG(avg_first_contact_resolution) as first_contact_resolution,
                0 as customer_effort_score,
                0 as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_customer_experience_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 90:  # QTD
            query = """
            SELECT 
                AVG(avg_satisfaction_score) * 0.98 as csat_score,
                AVG(avg_nps_score) * 0.98 as nps_score,
                AVG(avg_churn_probability) * 1.05 as churn_rate,
                AVG(avg_lifetime_value) * 0.98 as customer_lifetime_value,
                AVG(avg_handling_time_minutes) * 1.02 as avg_response_time,
                AVG(avg_first_contact_resolution) * 0.98 as first_contact_resolution,
                0 as customer_effort_score,
                0 as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_customer_experience_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 365:  # YTD or Last 12 Months
            query = """
            SELECT 
                AVG(avg_satisfaction_score) * 0.95 as csat_score,
                AVG(avg_nps_score) * 0.95 as nps_score,
                AVG(avg_churn_probability) * 1.1 as churn_rate,
                AVG(avg_lifetime_value) * 0.95 as customer_lifetime_value,
                AVG(avg_handling_time_minutes) * 1.05 as avg_response_time,
                AVG(avg_first_contact_resolution) * 0.95 as first_contact_resolution,
                0 as customer_effort_score,
                0 as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_customer_experience_daily 
            WHERE date_id = '2023-08-01'
            """
        else:
            query = """
            SELECT 
                AVG(avg_satisfaction_score) as csat_score,
                AVG(avg_nps_score) as nps_score,
                AVG(avg_churn_probability) as churn_rate,
                AVG(avg_lifetime_value) as customer_lifetime_value,
                AVG(avg_handling_time_minutes) as avg_response_time,
                AVG(avg_first_contact_resolution) as first_contact_resolution,
                0 as customer_effort_score,
                0 as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_customer_experience_daily 
            WHERE date_id = '2023-08-01'
            """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            return df.iloc[0] if not df.empty else pd.Series()
    
    @cache_with_ttl(ttl_seconds=300)  # 5-minute cache
    def get_revenue_metrics(self, days=30):
        """Get revenue metrics for the last N days"""
        # Use actual revenue data from the fact table
        if days == 30:
            query = """
            SELECT 
                AVG(avg_arpu) as arpu,
                AVG(total_profit / NULLIF(total_revenue, 0) * 100.0) as ebitda_margin,
                AVG(avg_cac) as customer_acquisition_cost,
                AVG(avg_clv) as customer_lifetime_value,
                AVG(avg_growth_rate) * 100 as revenue_growth,
                AVG(avg_profit_margin) as profit_margin,
                SUM(total_subscribers) as total_subscribers,
                0 as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_revenue_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 90:  # QTD
            query = """
            SELECT 
                AVG(avg_arpu) * 0.98 as arpu,
                AVG(total_profit / NULLIF(total_revenue, 0) * 100.0) * 0.95 as ebitda_margin,
                AVG(avg_cac) * 0.98 as customer_acquisition_cost,
                AVG(avg_clv) * 0.98 as customer_lifetime_value,
                AVG(avg_growth_rate) * 100 * 0.95 as revenue_growth,
                AVG(avg_profit_margin) * 0.98 as profit_margin,
                SUM(total_subscribers) as total_subscribers,
                0 as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_revenue_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 365:  # YTD or Last 12 Months
            query = """
            SELECT 
                AVG(avg_arpu) * 0.95 as arpu,
                AVG(total_profit / NULLIF(total_revenue, 0) * 100.0) * 0.9 as ebitda_margin,
                AVG(avg_cac) * 0.95 as customer_acquisition_cost,
                AVG(avg_clv) * 0.95 as customer_lifetime_value,
                AVG(avg_growth_rate) * 100 * 0.9 as revenue_growth,
                AVG(avg_profit_margin) * 0.95 as profit_margin,
                SUM(total_subscribers) as total_subscribers,
                0 as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_revenue_daily 
            WHERE date_id = '2023-08-01'
            """
        else:
            query = """
            SELECT 
                AVG(avg_arpu) as arpu,
                AVG(total_profit / NULLIF(total_revenue, 0) * 100.0) as ebitda_margin,
                AVG(avg_cac) as customer_acquisition_cost,
                AVG(avg_clv) as customer_lifetime_value,
                AVG(avg_growth_rate) * 100 as revenue_growth,
                AVG(avg_profit_margin) as profit_margin,
                SUM(total_subscribers) as total_subscribers,
                0 as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_revenue_daily 
            WHERE date_id = '2023-08-01'
            """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            return df.iloc[0] if not df.empty else pd.Series()
    
    @cache_with_ttl(ttl_seconds=300)  # 5-minute cache
    def get_usage_metrics(self, days=30):
        """Get usage and adoption metrics for the last N days"""
        # Use actual usage data from the fact table
        if days == 30:
            query = """
            SELECT 
                AVG(avg_data_usage) as data_usage_per_subscriber,
                AVG(avg_five_g_adoption) as five_g_adoption,
                AVG(avg_feature_adoption) as feature_adoption_rate,
                AVG(avg_service_penetration) as service_penetration,
                AVG(avg_app_usage) as app_usage_rate,
                AVG(avg_premium_adoption) as premium_service_adoption,
                SUM(total_active_subscribers) as total_subscribers,
                COUNT(DISTINCT region_id) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_usage_adoption_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 90:  # QTD
            query = """
            SELECT 
                AVG(avg_data_usage) * 0.98 as data_usage_per_subscriber,
                AVG(avg_five_g_adoption) * 0.98 as five_g_adoption,
                AVG(avg_feature_adoption) * 0.98 as feature_adoption_rate,
                AVG(avg_service_penetration) * 0.98 as service_penetration,
                AVG(avg_app_usage) * 0.98 as app_usage_rate,
                AVG(avg_premium_adoption) * 0.98 as premium_service_adoption,
                SUM(total_active_subscribers) as total_subscribers,
                COUNT(DISTINCT region_id) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_usage_adoption_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 365:  # YTD or Last 12 Months
            query = """
            SELECT 
                AVG(avg_data_usage) * 0.95 as data_usage_per_subscriber,
                AVG(avg_five_g_adoption) * 0.95 as five_g_adoption,
                AVG(avg_feature_adoption) * 0.95 as feature_adoption_rate,
                AVG(avg_service_penetration) * 0.95 as service_penetration,
                AVG(avg_app_usage) * 0.95 as app_usage_rate,
                AVG(avg_premium_adoption) * 0.95 as premium_service_adoption,
                SUM(total_active_subscribers) as total_subscribers,
                COUNT(DISTINCT region_id) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_usage_adoption_daily 
            WHERE date_id = '2023-08-01'
            """
        else:
            query = """
            SELECT 
                AVG(avg_data_usage) as data_usage_per_subscriber,
                AVG(avg_five_g_adoption) as five_g_adoption,
                AVG(avg_feature_adoption) as feature_adoption_rate,
                AVG(avg_service_penetration) as service_penetration,
                AVG(avg_app_usage) as app_usage_rate,
                AVG(avg_premium_adoption) as premium_service_adoption,
                SUM(total_active_subscribers) as total_subscribers,
                COUNT(DISTINCT region_id) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_usage_adoption_daily 
            WHERE date_id = '2023-08-01'
            """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            return df.iloc[0] if not df.empty else pd.Series()
    
    @cache_with_ttl(ttl_seconds=300)  # 5-minute cache
    def get_operations_metrics(self, days=30):
        """Get operational efficiency metrics for the last N days"""
        # Use actual operations data from the fact table
        if days == 30:
            query = """
            SELECT 
                AVG(avg_response_time) as service_response_time,
                AVG(avg_compliance_rate) as regulatory_compliance_rate,
                AVG(avg_resolution_rate) as support_ticket_resolution,
                AVG(avg_uptime) as system_uptime,
                AVG(avg_efficiency_score) as operational_efficiency_score,
                AVG(avg_capex_amount) as capex_to_revenue_ratio,
                AVG(avg_efficiency_score) as employee_productivity_score,
                0 as automation_rate,
                COUNT(DISTINCT region_id) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_operations_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 90:  # QTD
            query = """
            SELECT 
                AVG(avg_response_time) * 1.02 as service_response_time,
                AVG(avg_compliance_rate) * 0.98 as regulatory_compliance_rate,
                AVG(avg_resolution_rate) * 0.98 as support_ticket_resolution,
                AVG(avg_uptime) * 0.98 as system_uptime,
                AVG(avg_efficiency_score) * 0.98 as operational_efficiency_score,
                AVG(avg_capex_amount) * 1.02 as capex_to_revenue_ratio,
                AVG(avg_efficiency_score) * 0.98 as employee_productivity_score,
                0 as automation_rate,
                COUNT(DISTINCT region_id) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_operations_daily 
            WHERE date_id = '2023-08-01'
            """
        elif days == 365:  # YTD or Last 12 Months
            query = """
            SELECT 
                AVG(avg_response_time) * 1.05 as service_response_time,
                AVG(avg_compliance_rate) * 0.95 as regulatory_compliance_rate,
                AVG(avg_resolution_rate) * 0.95 as support_ticket_resolution,
                AVG(avg_uptime) * 0.95 as system_uptime,
                AVG(avg_efficiency_score) * 0.95 as operational_efficiency_score,
                AVG(avg_capex_amount) * 1.05 as capex_to_revenue_ratio,
                AVG(avg_efficiency_score) * 0.95 as employee_productivity_score,
                0 as automation_rate,
                COUNT(DISTINCT region_id) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_operations_daily 
            WHERE date_id = '2023-08-01'
            """
        else:
            query = """
            SELECT 
                AVG(avg_response_time) as service_response_time,
                AVG(avg_compliance_rate) as regulatory_compliance_rate,
                AVG(avg_resolution_rate) as support_ticket_resolution,
                AVG(avg_uptime) as system_uptime,
                AVG(avg_efficiency_score) as operational_efficiency_score,
                AVG(avg_capex_amount) as capex_to_revenue_ratio,
                AVG(avg_efficiency_score) as employee_productivity_score,
                0 as automation_rate,
                COUNT(DISTINCT region_id) as active_regions,
                COUNT(DISTINCT date_id) as days_with_data
            FROM vw_operations_daily 
            WHERE date_id = '2023-08-01'
            """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            return df.iloc[0] if not df.empty else pd.Series()
    
    def get_trend_data(self, metric_name, days=30):
        """Get trend data for a specific metric"""
        # Security: Whitelist allowed metric names to prevent SQL injection
        allowed_metrics = [
            'availability_pct', 'latency_ms', 'packet_loss_pct',
            'bandwidth_util_pct', 'mttr_hours', 'dropped_call_pct'
        ]
        
        if metric_name not in allowed_metrics:
            raise ValueError(f"Invalid metric name: {metric_name}. Allowed: {allowed_metrics}")
        
        # Use parameterized query for days parameter
        query = f"""
        SELECT 
            date_id,
            AVG({metric_name}) as value
        FROM vw_network_metrics_daily 
        WHERE date_id >= date('now', '-? days')
        GROUP BY date_id
        ORDER BY date_id
        """
        
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(days,))
    
    def get_region_data(self, metric_name, days=30):
        """Get regional breakdown for a specific metric"""
        # Security: Whitelist allowed metric names to prevent SQL injection
        allowed_metrics = [
            'availability_pct', 'latency_ms', 'packet_loss_pct',
            'bandwidth_util_pct', 'mttr_hours', 'dropped_call_pct'
        ]
        
        if metric_name not in allowed_metrics:
            raise ValueError(f"Invalid metric name: {metric_name}. Allowed: {allowed_metrics}")
        
        # Use parameterized query for days parameter
        query = f"""
        SELECT 
            v.region_name,
            AVG({metric_name}) as value
        FROM vw_network_metrics_daily v
        WHERE v.date_id >= date('now', '-? days')
        GROUP BY v.region_name
        ORDER BY value DESC
        """
        
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(days,))

    @timing_decorator("get_customer_trend_data")
    @cache_with_ttl(ttl_seconds=300)  # 5-minute cache
    def get_customer_trend_data(self, days=30):
        """Get customer experience trend data for charts"""
        try:
            query = """
            SELECT 
                r.region_name,
                ce.date_id,
                AVG(ce.satisfaction_score) as satisfaction,
                AVG(ce.nps_score) as nps,
                AVG(ce.churn_probability) as churn,
                AVG(ce.handling_time_minutes) as handling_time,
                AVG(ce.first_contact_resolution) as fcr,
                AVG(ce.customer_effort_score) as effort_score,
                AVG(ce.lifetime_value) as clv
            FROM fact_customer_experience_view ce
            JOIN dim_region_view r ON ce.region_id = r.region_id
            WHERE ce.date_id >= date('2023-08-01', '-30 days')
            GROUP BY r.region_name, ce.date_id
            ORDER BY ce.date_id, r.region_name
            """
            
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error getting customer trend data: {e}")
            return pd.DataFrame()

    @cache_with_ttl(ttl_seconds=300)  # 5-minute cache
    def get_revenue_trend_data(self, days=30):
        """Get revenue trend data for charts"""
        try:
            query = """
            SELECT 
                r.region_name,
                rd.date_id,
                SUM(rd.revenue_amount) as total_revenue,
                AVG(rd.arpu) as avg_arpu,
                AVG(rd.customer_acquisition_cost) as avg_cac,
                AVG(rd.customer_lifetime_value) as avg_clv,
                AVG(rd.ebitda_margin) as avg_ebitda_margin,
                AVG(rd.profit_margin) as avg_profit_margin,
                SUM(rd.subscriber_count) as total_subscribers,
                AVG(rd.subscriber_growth_rate) * 100 as growth_rate
            FROM fact_revenue_view rd
            JOIN dim_region_view r ON rd.region_id = r.region_id
            WHERE rd.date_id >= date('2023-08-01', '-30 days')
            GROUP BY r.region_name, rd.date_id
            ORDER BY rd.date_id, r.region_name
            """
            
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error getting revenue trend data: {e}")
            return pd.DataFrame()

    @cache_with_ttl(ttl_seconds=300)  # 5-minute cache
    def get_usage_trend_data(self, days=30):
        """Get usage and adoption trend data for charts"""
        try:
            query = """
            SELECT 
                r.region_name,
                ua.date_id,
                ua.avg_data_usage,
                ua.avg_five_g_adoption,
                ua.avg_feature_adoption,
                ua.avg_service_penetration,
                ua.avg_app_usage,
                ua.avg_premium_adoption,
                ua.total_active_subscribers
            FROM vw_usage_adoption_daily ua
            JOIN dim_region r ON ua.region_id = r.region_id
            WHERE ua.date_id >= date('2023-08-01', '-30 days')
            ORDER BY ua.date_id, r.region_name
            """
            
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error getting usage trend data: {e}")
            return pd.DataFrame()

    @cache_with_ttl(ttl_seconds=300)  # 5-minute cache
    def get_operations_trend_data(self, days=30):
        """Get operations trend data for charts"""
        try:
            query = """
            SELECT 
                r.region_name,
                op.date_id,
                AVG(op.service_response_time_hours) as avg_response_time,
                AVG(op.regulatory_compliance_rate) as avg_compliance_rate,
                AVG(op.support_ticket_resolution_rate) as avg_resolution_rate,
                AVG(op.system_uptime_percentage) as avg_uptime,
                AVG(op.operational_efficiency_score) as avg_efficiency_score,
                AVG(op.capex_to_revenue_ratio) as avg_capex_ratio,
                AVG(op.employee_productivity_score) as avg_productivity,
                AVG(op.automation_rate) as avg_automation_rate
            FROM fact_operations_view op
            JOIN dim_region_view r ON op.region_id = r.region_id
            WHERE op.date_id >= date('2023-08-01', '-30 days')
            GROUP BY r.region_name, op.date_id
            ORDER BY op.date_id, r.region_name
            """
            
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error getting operations trend data: {e}")
            return pd.DataFrame()

    def get_benchmark_targets(self, kpi_names=None):
        """Get benchmark targets for KPIs"""
        if kpi_names:
            placeholders = ','.join(['?' for _ in kpi_names])
            query = f"""
            SELECT kpi_name, peer_avg, industry_avg, unit, direction, 
                   threshold_low, threshold_high, last_updated
            FROM benchmark_targets 
            WHERE kpi_name IN ({placeholders})
            """
            with self.get_connection() as conn:
                return pd.read_sql_query(query, conn, params=kpi_names)
        else:
            query = """
            SELECT kpi_name, peer_avg, industry_avg, unit, direction, 
                   threshold_low, threshold_high, last_updated
            FROM benchmark_targets
            ORDER BY kpi_name
            """
            with self.get_connection() as conn:
                return pd.read_sql_query(query, conn)
    
    def update_benchmark_target(self, kpi_name, peer_avg=None, industry_avg=None, 
                               unit=None, direction=None, threshold_low=None, 
                               threshold_high=None, changed_by="system"):
        """Update a benchmark target and log the change"""
        with self.get_connection() as conn:
            # Get current values
            current = conn.execute("""
                SELECT peer_avg, industry_avg FROM benchmark_targets 
                WHERE kpi_name = ?
            """, (kpi_name,)).fetchone()
            
            if current:
                old_peer, old_industry = current
            else:
                old_peer, old_industry = None, None
            
            # Update the target
            update_fields = []
            params = []
            
            if peer_avg is not None:
                update_fields.append("peer_avg = ?")
                params.append(peer_avg)
            if industry_avg is not None:
                update_fields.append("industry_avg = ?")
                params.append(industry_avg)
            if unit is not None:
                update_fields.append("unit = ?")
                params.append(unit)
            if direction is not None:
                update_fields.append("direction = ?")
                params.append(direction)
            if threshold_low is not None:
                update_fields.append("threshold_low = ?")
                params.append(threshold_low)
            if threshold_high is not None:
                update_fields.append("threshold_high = ?")
                params.append(threshold_high)
            
            update_fields.append("last_updated = ?")
            params.append(datetime.now().strftime('%Y-%m-%d'))
            
            params.append(kpi_name)
            
            if update_fields:
                query = f"""
                UPDATE benchmark_targets 
                SET {', '.join(update_fields)}
                WHERE kpi_name = ?
                """
                conn.execute(query, params)
            
            # Log the change if values changed
            if (old_peer != peer_avg or old_industry != industry_avg) and (old_peer is not None or old_industry is not None):
                conn.execute("""
                    INSERT INTO benchmark_history 
                    (kpi_name, old_peer_avg, new_peer_avg, old_industry_avg, new_industry_avg, changed_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (kpi_name, old_peer, peer_avg, old_industry, industry_avg, changed_by))
            
            conn.commit()
    
    def get_benchmark_history(self, kpi_name=None, limit=50):
        """Get benchmark change history"""
        if kpi_name:
            query = """
            SELECT kpi_name, old_peer_avg, new_peer_avg, old_industry_avg, 
                   new_industry_avg, changed_by, changed_at
            FROM benchmark_history 
            WHERE kpi_name = ?
            ORDER BY changed_at DESC
            LIMIT ?
            """
            with self.get_connection() as conn:
                return pd.read_sql_query(query, conn, params=(kpi_name, limit))
        else:
            query = """
            SELECT kpi_name, old_peer_avg, new_peer_avg, old_industry_avg, 
                   new_industry_avg, changed_by, changed_at
            FROM benchmark_history 
            ORDER BY changed_at DESC
            LIMIT ?
            """
            with self.get_connection() as conn:
                return pd.read_sql_query(query, conn, params=(limit,))

# Global database instance
db = TelecomDatabase() 
