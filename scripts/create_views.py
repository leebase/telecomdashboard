#!/usr/bin/env python3
"""
View Creation Script for Telecom Metadata Runtime

This script creates standardized database views for all telecom data tables,
providing a clean abstraction layer between the application and physical data structures.
Supports both SQLite (development) and Snowflake (production) databases.

Usage:
    python scripts/create_views.py                    # Create views in SQLite
    python scripts/create_views.py --snowflake       # Create views in Snowflake
    python scripts/create_views.py --drop            # Drop existing views
    python scripts/create_views.py --list            # List existing views
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Only import DataSourceFactory for Snowflake operations
DataSourceFactory = None
try:
    from src.data.datasource import DataSourceFactory
except ImportError:
    # Fallback for when dependencies are not available
    pass


class ViewCreator:
    """Creates standardized database views for telecom data abstraction."""

    def __init__(self, db_type: str = 'sqlite'):
        self.db_type = db_type
        self.factory = DataSourceFactory if DataSourceFactory else None
        self.connection = None

    def get_view_definitions(self) -> Dict[str, str]:
        """Get all view definitions for the telecom schema."""

        views = {}

        # Dimension Views
        views['dim_time_view'] = """
            SELECT
                date_id,
                hour,
                year,
                month,
                day,
                weekday,
                is_weekend
            FROM dim_time
        """

        views['dim_region_view'] = """
            SELECT
                region_id,
                region_name
            FROM dim_region
        """

        views['dim_network_element_view'] = """
            SELECT
                network_element_id,
                element_name,
                element_type,
                vendor,
                install_date,
                region_id
            FROM dim_network_element
        """

        views['dim_product_view'] = """
            SELECT
                product_id,
                product_name,
                product_category,
                product_type,
                price_monthly,
                data_limit_gb AS data_allowance_gb,
                CASE WHEN is_premium THEN 'premium' ELSE 'standard' END AS features
            FROM dim_product
        """

        views['dim_employee_view'] = """
            SELECT
                employee_id,
                employee_name,
                department,
                role,
                hire_date,
                region_id,
                CASE WHEN is_active THEN 'active' ELSE 'inactive' END AS status
            FROM dim_employee
        """

        views['dim_channel_view'] = """
            SELECT
                channel_id,
                channel_name,
                channel_type,
                channel_category,
                is_digital,
                cost_per_interaction
            FROM dim_channel
        """

        views['dim_customer_view'] = """
            SELECT
                customer_id,
                customer_type AS customer_name,
                segment,
                region_id,
                acquisition_date AS signup_date,
                'active' AS status,
                contract_type
            FROM dim_customer
        """

        # Fact Table Views
        views['fact_network_metrics_view'] = """
            SELECT
                network_element_id,
                region_id,
                date_id,
                uptime_seconds,
                downtime_seconds,
                latency_ms,
                packet_loss_percent,
                bandwidth_utilization_percent,
                mttr_hours,
                dropped_call_rate
            FROM fact_network_metrics
        """

        views['fact_customer_experience_view'] = """
            SELECT
                date_id,
                customer_id,
                region_id,
                channel_id,
                satisfaction_score,
                nps_score,
                churn_probability,
                handling_time_minutes,
                first_contact_resolution,
                complaint_count,
                escalation_count,
                customer_effort_score,
                lifetime_value
            FROM fact_customer_experience
        """

        views['fact_revenue_view'] = """
            SELECT
                date_id,
                customer_id,
                product_id,
                region_id,
                channel_id,
                revenue_amount,
                arpu,
                customer_acquisition_cost,
                customer_lifetime_value,
                churn_revenue_loss,
                upsell_revenue,
                cross_sell_revenue,
                ebitda_margin,
                profit_margin,
                subscriber_count,
                subscriber_growth_rate
            FROM fact_revenue
        """

        views['fact_usage_adoption_view'] = """
            SELECT
                date_id,
                customer_id,
                product_id,
                region_id,
                data_usage_gb,
                voice_minutes,
                sms_count,
                feature_adoption_rate,
                five_g_adoption,
                service_penetration,
                app_usage_rate,
                premium_service_adoption,
                peak_usage_time,
                average_session_duration,
                active_subscribers
            FROM fact_usage_adoption
        """

        views['fact_operations_view'] = """
            SELECT
                date_id,
                region_id,
                employee_id,
                channel_id,
                service_response_time_hours,
                regulatory_compliance_rate,
                support_ticket_resolution_rate,
                system_uptime_percentage,
                operational_efficiency_score,
                capex_to_revenue_ratio,
                employee_productivity_score,
                cost_per_customer,
                automation_rate,
                training_completion_rate,
                incident_count,
                resolution_time_hours
            FROM fact_operations
        """

        # Business Views (Daily Aggregations)
        views['vw_network_metrics_daily'] = """
            SELECT
                f.date_id,
                r.region_name,
                AVG(100.0 * f.uptime_seconds / NULLIF(f.uptime_seconds + f.downtime_seconds, 0)) as availability_pct,
                AVG(f.latency_ms) as latency_ms,
                AVG(f.packet_loss_percent) as packet_loss_pct,
                AVG(f.bandwidth_utilization_percent) as bandwidth_util_pct,
                AVG(f.dropped_call_rate) as dropped_call_pct,
                AVG(f.mttr_hours) as mttr_hours
            FROM fact_network_metrics_view f
            JOIN dim_region_view r ON r.region_id = f.region_id
            GROUP BY f.date_id, r.region_name
        """

        views['vw_customer_experience_daily'] = """
            SELECT
                f.date_id,
                AVG(f.satisfaction_score) as avg_satisfaction_score,
                AVG(f.nps_score) as avg_nps_score,
                AVG(f.churn_probability) as avg_churn_probability,
                AVG(f.handling_time_minutes) as avg_handling_time_minutes,
                AVG(f.first_contact_resolution) as avg_first_contact_resolution,
                AVG(f.lifetime_value) as avg_lifetime_value
            FROM fact_customer_experience_view f
            GROUP BY f.date_id
        """

        views['vw_revenue_daily'] = """
            SELECT
                f.date_id,
                SUM(f.revenue_amount) as total_revenue,
                SUM(f.customer_acquisition_cost) as total_cost,
                SUM(f.revenue_amount - f.customer_acquisition_cost) as total_profit,
                SUM(f.subscriber_count) as total_subscribers,
                AVG(f.arpu) as avg_arpu,
                AVG(f.customer_acquisition_cost) as avg_cac,
                AVG(f.customer_lifetime_value) as avg_clv,
                AVG(f.subscriber_growth_rate) as avg_growth_rate,
                AVG(f.profit_margin) as avg_profit_margin
            FROM fact_revenue_view f
            GROUP BY f.date_id
        """

        views['vw_usage_adoption_daily'] = """
            SELECT
                f.date_id,
                r.region_id,
                SUM(f.active_subscribers) as total_active_subscribers,
                AVG(f.data_usage_gb) as avg_data_usage,
                AVG(f.five_g_adoption) as avg_five_g_adoption,
                AVG(f.feature_adoption_rate) as avg_feature_adoption,
                AVG(f.service_penetration) as avg_service_penetration,
                AVG(f.app_usage_rate) as avg_app_usage,
                AVG(f.premium_service_adoption) as avg_premium_adoption
            FROM fact_usage_adoption_view f
            JOIN dim_region_view r ON r.region_id = f.region_id
            GROUP BY f.date_id, r.region_id
        """

        views['vw_operations_daily'] = """
            SELECT
                f.date_id,
                r.region_id,
                AVG(f.service_response_time_hours) as avg_response_time,
                AVG(f.regulatory_compliance_rate) as avg_compliance_rate,
                AVG(f.capex_to_revenue_ratio) as avg_capex_amount,
                AVG(f.operational_efficiency_score) as avg_efficiency_score,
                AVG(f.support_ticket_resolution_rate) as avg_resolution_rate,
                AVG(f.system_uptime_percentage) as avg_uptime,
                SUM(f.incident_count) as total_incidents
            FROM fact_operations_view f
            JOIN dim_region_view r ON r.region_id = f.region_id
            GROUP BY f.date_id, r.region_id
        """

        # Benchmark Views
        views['benchmark_targets_view'] = """
            SELECT
                kpi_name,
                peer_avg,
                industry_avg,
                unit,
                direction,
                threshold_low,
                threshold_high,
                last_updated
            FROM benchmark_targets
        """

        views['benchmark_history_view'] = """
            SELECT
                kpi_name,
                old_peer_avg,
                new_peer_avg,
                old_industry_avg,
                new_industry_avg,
                changed_by,
                changed_at
            FROM benchmark_history
        """

        return views

    def create_views_sqlite(self, views: Dict[str, str]) -> List[str]:
        """Generate SQLite-specific view creation SQL."""
        sql_statements = []

        for view_name, view_sql in views.items():
            create_sql = f"CREATE VIEW IF NOT EXISTS {view_name} AS {view_sql.strip()}"
            sql_statements.append(create_sql)

        return sql_statements

    def create_views_snowflake(self, views: Dict[str, str]) -> List[str]:
        """Generate Snowflake-specific view creation SQL."""
        sql_statements = []

        for view_name, view_sql in views.items():
            # Snowflake view creation with security
            create_sql = f"""
                CREATE OR REPLACE SECURE VIEW {view_name} AS
                {view_sql.strip()}
            """
            sql_statements.append(create_sql)

        return sql_statements

    def execute_sql(self, sql_statements: List[str]) -> bool:
        """Execute SQL statements against the database."""
        try:
            if self.db_type == 'sqlite':
                # Use direct SQLite connection for view creation
                db_path = Path(__file__).parent.parent / 'data' / 'telecom_db.sqlite'
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                for sql in sql_statements:
                    cursor.execute(sql)

                conn.commit()
                conn.close()
                return True

            elif self.db_type == 'snowflake':
                # Use datasource factory for Snowflake
                if not self.factory:
                    print("❌ DataSourceFactory not available. Cannot create Snowflake views.")
                    return False
                datasource = self.factory.create_datasource('snowflake_main')
                with datasource.get_connection() as conn:
                    cursor = conn.cursor()
                    for sql in sql_statements:
                        cursor.execute(sql)
                    conn.commit()
                return True

        except Exception as e:
            print(f"Error executing SQL: {e}")
            return False

    def drop_views(self, views: Dict[str, str]) -> bool:
        """Drop existing views."""
        try:
            if self.db_type == 'sqlite':
                db_path = Path(__file__).parent.parent / 'data' / 'telecom_db.sqlite'
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                for view_name in views.keys():
                    cursor.execute(f"DROP VIEW IF EXISTS {view_name}")

                conn.commit()
                conn.close()
                return True

            elif self.db_type == 'snowflake':
                if not self.factory:
                    print("❌ DataSourceFactory not available. Cannot drop Snowflake views.")
                    return False
                datasource = self.factory.create_datasource('snowflake_main')
                with datasource.get_connection() as conn:
                    cursor = conn.cursor()
                    for view_name in views.keys():
                        cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
                    conn.commit()
                return True

        except Exception as e:
            print(f"Error dropping views: {e}")
            return False

    def list_views(self) -> List[str]:
        """List existing views in the database."""
        try:
            if self.db_type == 'sqlite':
                db_path = Path(__file__).parent.parent / 'data' / 'telecom_db.sqlite'
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
                views = [row[0] for row in cursor.fetchall()]
                conn.close()
                return views

            elif self.db_type == 'snowflake':
                if not self.factory:
                    print("❌ DataSourceFactory not available. Cannot list Snowflake views.")
                    return []
                datasource = self.factory.create_datasource('snowflake_main')
                with datasource.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SHOW VIEWS")
                    views = [row[1] for row in cursor.fetchall()]
                return views

        except Exception as e:
            print(f"Error listing views: {e}")
            return []


def main():
    parser = argparse.ArgumentParser(description='Create database views for telecom metadata runtime')
    parser.add_argument('--snowflake', action='store_true', help='Create views in Snowflake instead of SQLite')
    parser.add_argument('--drop', action='store_true', help='Drop existing views')
    parser.add_argument('--list', action='store_true', help='List existing views')

    args = parser.parse_args()

    db_type = 'snowflake' if args.snowflake else 'sqlite'
    creator = ViewCreator(db_type)

    if args.list:
        views = creator.list_views()
        print(f"Existing views in {db_type}:")
        for view in views:
            print(f"  - {view}")
        return

    views = creator.get_view_definitions()

    if args.drop:
        print(f"Dropping views in {db_type}...")
        if creator.drop_views(views):
            print("✅ Views dropped successfully")
        else:
            print("❌ Failed to drop views")
        return

    # Create views
    print(f"Creating {len(views)} views in {db_type}...")

    if db_type == 'sqlite':
        sql_statements = creator.create_views_sqlite(views)
    else:
        sql_statements = creator.create_views_snowflake(views)

    if creator.execute_sql(sql_statements):
        print(f"✅ Successfully created {len(views)} views in {db_type}")
        print("\nCreated views:")
        for view_name in views.keys():
            print(f"  - {view_name}")
    else:
        print("❌ Failed to create views")
        sys.exit(1)


if __name__ == '__main__':
    main()
