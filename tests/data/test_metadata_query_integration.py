"""
Integration tests for metadata pack queries against actual database.

These tests execute the actual SQL queries from the metadata pack
against the database to catch column mismatches and other issues
before they reach production.
"""

import sqlite3
import pytest
from pathlib import Path
from typing import Dict, List

import sys
sys.path.insert(0, 'src')

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
class TestMetadataQueryIntegration:
    """Integration tests for metadata pack queries."""

    @pytest.fixture
    def db_conn(self):
        """Database connection fixture."""
        db_path = Path("data/telecom_db.sqlite")
        if not db_path.exists():
            pytest.skip("Database file not found")

        conn = sqlite3.connect(str(db_path))
        yield conn
        conn.close()

    @pytest.fixture
    def metadata_pack(self):
        """Load metadata pack fixture."""
        metadata_path = Path("metadata/dashboard_telco.yaml")
        if not metadata_path.exists():
            pytest.skip("Metadata pack not found")

        with open(metadata_path, 'r') as f:
            return yaml.safe_load(f)

    def test_all_kpi_queries_execute_without_errors(self, db_conn, metadata_pack):
        """Test that all KPI queries in metadata pack execute without SQL errors."""
        cursor = db_conn.cursor()

        failed_queries = []

        for kpi in metadata_pack.get('kpis', []):
            for metric in kpi.get('metrics', []):
                sql = metric.get('sql', '').strip()
                if not sql:
                    continue

                try:
                    # Test with a sample date range that should work
                    test_sql = sql.replace(
                        '{{ date_range.start }}', "'2025-08-22'"
                    ).replace(
                        '{{ date_range.end }}', "'2025-09-20'"
                    )

                    cursor.execute(f"EXPLAIN QUERY PLAN {test_sql}")
                    # If we get here, the query is syntactically valid

                except sqlite3.OperationalError as e:
                    if "no such column" in str(e):
                        failed_queries.append({
                            'kpi': kpi['id'],
                            'metric': metric.get('id', 'unknown'),
                            'error': str(e),
                            'sql': sql
                        })
                    elif "unrecognized token" in str(e) and "{" in str(e):
                        # Skip template processing errors - these are expected in raw SQL testing
                        # The templates will be processed by the actual application
                        pass
                    else:
                        # Other SQL errors are concerning
                        failed_queries.append({
                            'kpi': kpi['id'],
                            'metric': metric.get('id', 'unknown'),
                            'error': str(e),
                            'sql': sql
                        })

        if failed_queries:
            error_msg = "Found KPI queries with errors:\n"
            for failure in failed_queries:
                error_msg += f"\nKPI: {failure['kpi']}\n"
                error_msg += f"Metric: {failure['metric']}\n"
                error_msg += f"Error: {failure['error']}\n"
                error_msg += f"SQL: {failure['sql'][:100]}...\n"

            pytest.fail(error_msg)

    def test_view_columns_exist_for_metadata_queries(self, db_conn, metadata_pack):
        """Test that all columns referenced in metadata queries exist in views."""
        cursor = db_conn.cursor()

        # Get all view columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        view_names = [row[0] for row in cursor.fetchall()]

        view_columns = {}
        for view_name in view_names:
            cursor.execute(f"PRAGMA table_info({view_name})")
            columns = [row[1] for row in cursor.fetchall()]
            view_columns[view_name] = set(columns)

        missing_columns = []

        for kpi in metadata_pack.get('kpis', []):
            for metric in kpi.get('metrics', []):
                sql = metric.get('sql', '')
                if not sql or 'FROM' not in sql.upper():
                    continue

                # Extract view name
                lines = sql.strip().split('\n')
                from_line = [line for line in lines if 'FROM' in line.upper()]
                if from_line:
                    view_name = from_line[0].split()[-1].strip()
                    if view_name in view_columns:
                        # Check for AVG(column_name) patterns
                        import re
                        avg_pattern = r'AVG\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)'
                        matches = re.findall(avg_pattern, sql, re.IGNORECASE)

                        for col_name in matches:
                            if col_name not in view_columns[view_name]:
                                missing_columns.append({
                                    'kpi': kpi['id'],
                                    'view': view_name,
                                    'missing_column': col_name,
                                    'sql': sql
                                })

        if missing_columns:
            error_msg = "Found metadata queries referencing non-existent columns:\n"
            for missing in missing_columns:
                error_msg += f"\nKPI: {missing['kpi']}\n"
                error_msg += f"View: {missing['view']}\n"
                error_msg += f"Missing Column: {missing['missing_column']}\n"

            pytest.fail(error_msg)

    def test_business_views_have_expected_columns(self, db_conn):
        """Test that business views have the expected aggregated columns."""
        cursor = db_conn.cursor()

        expected_columns = {
            'vw_network_metrics_daily': ['date_id', 'region_name', 'availability_pct', 'latency_ms', 'packet_loss_pct', 'bandwidth_util_pct', 'dropped_call_pct', 'mttr_hours'],
            'vw_customer_experience_daily': ['date_id', 'avg_satisfaction_score', 'avg_nps_score', 'avg_churn_probability', 'avg_handling_time_minutes', 'avg_first_contact_resolution', 'avg_lifetime_value'],
            'vw_revenue_daily': ['date_id', 'total_revenue', 'total_cost', 'total_profit', 'total_subscribers', 'avg_arpu', 'avg_cac', 'avg_clv', 'avg_growth_rate', 'avg_profit_margin'],
            'vw_usage_adoption_daily': ['date_id', 'region_id', 'total_active_subscribers', 'avg_data_usage', 'avg_five_g_adoption', 'avg_feature_adoption', 'avg_service_penetration', 'avg_app_usage', 'avg_premium_adoption'],
            'vw_operations_daily': ['date_id', 'region_id', 'avg_response_time', 'avg_compliance_rate', 'avg_capex_amount', 'avg_efficiency_score', 'avg_resolution_rate', 'avg_uptime', 'total_incidents']
        }

        for view_name, expected_cols in expected_columns.items():
            try:
                cursor.execute(f"PRAGMA table_info({view_name})")
                actual_cols = [row[1] for row in cursor.fetchall()]

                missing_cols = set(expected_cols) - set(actual_cols)
                if missing_cols:
                    pytest.fail(f"View {view_name} missing expected columns: {missing_cols}")

            except sqlite3.OperationalError as e:
                pytest.fail(f"Business view {view_name} error: {e}")

    def test_metadata_pack_schema_consistency(self, metadata_pack):
        """Test that metadata pack follows expected schema patterns."""
        # Check that all KPIs have required fields
        for kpi in metadata_pack.get('kpis', []):
            assert 'id' in kpi, f"KPI missing id: {kpi}"
            assert 'title' in kpi, f"KPI {kpi.get('id', 'unknown')} missing title"
            assert 'subject_area' in kpi, f"KPI {kpi.get('id', 'unknown')} missing subject_area"

            # Check metrics
            for metric in kpi.get('metrics', []):
                assert 'data_source' in metric, f"Metric in KPI {kpi['id']} missing data_source"
                assert 'sql' in metric, f"Metric in KPI {kpi['id']} missing sql"

    def test_view_creation_idempotent(self, db_conn):
        """Test that running view creation multiple times doesn't break anything."""
        from scripts.create_views import ViewCreator

        creator = ViewCreator('sqlite')

        # Run view creation twice
        for _ in range(2):
            views = creator.get_view_definitions()
            sql_statements = creator.create_views_sqlite(views)

            # Execute the statements
            cursor = db_conn.cursor()
            for sql in sql_statements:
                cursor.execute(sql)
            db_conn.commit()

        # Verify views still exist and work
        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vw_network_metrics_daily")
        count = cursor.fetchone()[0]
        assert isinstance(count, int), "Views should still be functional after recreation"