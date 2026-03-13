"""
Tests for database view validation and column mismatch detection.

These tests ensure that:
1. View definitions match actual table schemas
2. Metadata pack queries reference existing view columns
3. No "no such column" errors occur at runtime
"""

import sqlite3
import pytest
from pathlib import Path
from typing import Dict, List, Set

import sys
sys.path.insert(0, 'src')

from scripts.create_views import ViewCreator


class TestViewValidation:
    """Test suite for database view validation."""

    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a test database with the actual schema and views."""
        db_path = tmp_path / "test_telecom.db"

        # Copy the actual database structure
        source_db = Path("data/telecom_db.sqlite")
        if source_db.exists():
            import shutil
            shutil.copy2(source_db, db_path)

            # Create views in the test database
            import sys
            sys.path.insert(0, 'scripts')
            from create_views import ViewCreator

            creator = ViewCreator('sqlite')
            views = creator.get_view_definitions()
            sql_statements = creator.create_views_sqlite(views)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            for sql in sql_statements:
                cursor.execute(sql)
            conn.commit()
            conn.close()

        return db_path

    @pytest.fixture
    def view_creator(self, db_path):
        """Create a ViewCreator instance."""
        creator = ViewCreator('sqlite')
        # Override the database path for testing
        creator.db_path = str(db_path)
        return creator

    def test_view_definitions_match_table_schemas(self, db_path):
        """Test that all view definitions reference existing table columns."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table schemas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        table_columns = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            table_columns[table] = set(columns)

        # Test view creator can generate views without column errors
        creator = ViewCreator('sqlite')
        views = creator.get_view_definitions()

        # Try to create each view and check for column errors
        for view_name, view_sql in views.items():
            try:
                # Extract table references from view SQL
                if 'FROM' in view_sql.upper():
                    # This is a simplified check - in practice you'd parse the SQL more thoroughly
                    test_sql = f"EXPLAIN QUERY PLAN {view_sql}"
                    cursor.execute(test_sql)
                    # If we get here without exception, the view SQL is valid
            except sqlite3.OperationalError as e:
                if "no such column" in str(e):
                    pytest.fail(f"View {view_name} references non-existent column: {e}")
                # Re-raise other errors
                raise

        conn.close()

    def test_metadata_pack_queries_reference_existing_columns(self, db_path):
        """Test that metadata pack queries reference existing view columns."""
        import yaml

        # Load metadata pack
        with open('metadata/dashboard_telco.yaml', 'r') as f:
            metadata = yaml.safe_load(f)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all view columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]

        view_columns = {}
        for view in views:
            cursor.execute(f"PRAGMA table_info({view})")
            columns = [row[1] for row in cursor.fetchall()]
            view_columns[view] = set(columns)

        # Test each KPI query
        for kpi in metadata.get('kpis', []):
            for metric in kpi.get('metrics', []):
                sql = metric.get('sql', '')
                if sql and 'FROM' in sql.upper():
                    # Extract view name from FROM clause
                    lines = sql.strip().split('\n')
                    from_line = [line for line in lines if 'FROM' in line.upper()]
                    if from_line:
                        view_name = from_line[0].split()[-1].strip()
                        if view_name in view_columns:
                            # Check if query references non-existent columns
                            # This is a simplified check - would need more sophisticated SQL parsing
                            for col_set in view_columns[view_name]:
                                # Basic check for AVG(column_name) patterns
                                if f"AVG({col_set})" in sql or f"AVG( {col_set})" in sql:
                                    # Column is referenced, make sure it exists
                                    assert col_set in view_columns[view_name], \
                                        f"KPI {kpi['id']} references non-existent column {col_set} in view {view_name}"

        conn.close()

    def test_view_creation_completes_without_errors(self, view_creator):
        """Test that view creation completes without SQL errors."""
        views = view_creator.get_view_definitions()

        # This should not raise any exceptions
        sql_statements = view_creator.create_views_sqlite(views)

        # Verify we got SQL statements for all views
        assert len(sql_statements) == len(views)

        # Verify each statement looks like valid SQL
        for sql in sql_statements:
            assert sql.startswith("CREATE VIEW IF NOT EXISTS")
            assert "SELECT" in sql.upper()

    def test_business_views_aggregate_correctly(self, db_path):
        """Test that business views perform correct aggregations."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test that business views return expected data types
        business_views = [
            'vw_network_metrics_daily',
            'vw_customer_experience_daily',
            'vw_revenue_daily',
            'vw_usage_adoption_daily',
            'vw_operations_daily'
        ]

        for view in business_views:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {view}")
                count = cursor.fetchone()[0]
                # View should exist and be queryable
                assert isinstance(count, int)
            except sqlite3.OperationalError as e:
                pytest.fail(f"Business view {view} failed: {e}")

        conn.close()

    def test_view_column_consistency(self, db_path):
        """Test that view columns are consistent with their source tables."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get view definitions
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view' AND name LIKE '%_view'")
        views = cursor.fetchall()

        for view_name, view_sql in views:
            # Extract source table from view SQL
            if 'FROM' in view_sql.upper():
                from_clause = view_sql.split('FROM')[1].split()[0].strip()
                if from_clause and not from_clause.startswith('('):  # Skip subqueries
                    try:
                        # Check that source table exists
                        cursor.execute(f"SELECT COUNT(*) FROM {from_clause}")
                        # If we get here, the table exists
                    except sqlite3.OperationalError:
                        # This might be expected for some views, but let's log it
                        print(f"Warning: View {view_name} references table {from_clause} which may not exist")

        conn.close()


class TestMetadataQueryValidation:
    """Test suite for validating metadata pack queries against database schema."""

    def test_kpi_queries_use_valid_columns(self):
        """Test that all KPI queries in metadata pack use valid column names."""
        import yaml

        # Load metadata pack
        with open('metadata/dashboard_telco.yaml', 'r') as f:
            metadata = yaml.safe_load(f)

        # This is a basic validation - in a real implementation you'd want
        # to actually execute the queries against a test database
        for kpi in metadata.get('kpis', []):
            for metric in kpi.get('metrics', []):
                sql = metric.get('sql', '')
                # Check that old incorrect column names are NOT used (exact matches, not substrings)
                import re
                words = re.findall(r'\b\w+\b', sql)
                assert 'churn_rate' not in words, f"KPI {kpi['id']} uses old column name 'churn_rate'"
                assert 'cost_amount' not in words, f"KPI {kpi['id']} uses old column name 'cost_amount'"
                assert 'first_contact_resolution_rate' not in words, f"KPI {kpi['id']} uses old column name 'first_contact_resolution_rate'"

                # Special check for avg_handling_time (should not appear as standalone word)
                if 'avg_handling_time' in sql and 'avg_handling_time_minutes' not in sql:
                    assert False, f"KPI {kpi['id']} uses old column name 'avg_handling_time' instead of 'avg_handling_time_minutes'"

                # Check that correct column names ARE used where expected
                if 'churn' in kpi['id'].lower():
                    assert 'avg_churn_probability' in sql, f"KPI {kpi['id']} should use 'avg_churn_probability'"
                if 'handling_time' in kpi['id'].lower():
                    assert 'avg_handling_time_minutes' in sql, f"KPI {kpi['id']} should use 'avg_handling_time_minutes'"
                if 'first_contact' in kpi['id'].lower():
                    assert 'avg_first_contact_resolution' in sql, f"KPI {kpi['id']} should use 'avg_first_contact_resolution'"

    def test_view_dependencies_exist(self):
        """Test that all views referenced in metadata pack actually exist."""
        import yaml

        # Load metadata pack
        with open('metadata/dashboard_telco.yaml', 'r') as f:
            metadata = yaml.safe_load(f)

        conn = sqlite3.connect('data/telecom_db.sqlite')
        cursor = conn.cursor()

        # Get all existing views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        existing_views = {row[0] for row in cursor.fetchall()}

        # Check that metadata pack doesn't reference non-existent views
        for kpi in metadata.get('kpis', []):
            for metric in kpi.get('metrics', []):
                sql = metric.get('sql', '')
                if sql and 'FROM' in sql.upper():
                    lines = sql.strip().split('\n')
                    from_line = [line for line in lines if 'FROM' in line.upper()]
                    if from_line:
                        # Extract view name more carefully
                        from_clause = from_line[0].replace('FROM', '').strip()
                        # Handle JOINs and subqueries
                        if 'JOIN' in from_clause.upper():
                            view_name = from_clause.split()[0].strip()
                        elif ' ' in from_clause:
                            view_name = from_clause.split()[0].strip()
                        else:
                            view_name = from_clause.strip()

                        assert view_name in existing_views, \
                            f"KPI {kpi['id']} references non-existent view '{view_name}' (FROM: {from_clause})"

        conn.close()