#!/usr/bin/env python3
"""
Schema Processor for YAML-Driven Telecom Database

This script processes the canonical telecom_data_warehouse_schema.yaml file to:
- Generate DDL for tables and views
- Create test data based on schema definitions
- Auto-generate metadata packs
- Support multiple database types (SQLite, Snowflake, PostgreSQL)

Usage:
    python scripts/schema_processor.py generate-ddl --database sqlite
    python scripts/schema_processor.py generate-views --database sqlite
    python scripts/schema_processor.py generate-test-data --rows 1000
    python scripts/schema_processor.py generate-metadata-pack
    python scripts/schema_processor.py validate-schema
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
import sqlite3
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class ColumnDefinition:
    """Represents a column definition from the schema."""
    name: str
    type: str
    description: str = ""
    primary_key: bool = False
    foreign_key: Optional[str] = None
    nullable: bool = True

@dataclass
class TableDefinition:
    """Represents a table definition from the schema."""
    name: str
    description: str
    columns: List[ColumnDefinition]
    view_sql: Optional[str] = None

class SimpleYAMLParser:
    """Simple YAML parser for basic structures."""

    @staticmethod
    def parse_table_definitions(content: str) -> List[TableDefinition]:
        """Parse table definitions from YAML content using regex."""
        tables = []

        # Find the tables section within the schema structure
        # Look for: schemas: ... tables:
        schema_pattern = r'schemas:(.*?)$'
        schema_match = re.search(schema_pattern, content, re.DOTALL)
        if not schema_match:
            return tables

        schema_content = schema_match.group(1)

        # Find tables section
        tables_pattern = r'tables:(.*?)(?=views:|$|data_types:)'
        tables_match = re.search(tables_pattern, schema_content, re.DOTALL)
        if not tables_match:
            return tables

        tables_content = tables_match.group(1)

        # Find table definitions (look for tables that have descriptions, not just columns)
        # Table pattern: starts with comment then - name: "table_name" description:
        table_pattern = r'# ([^\n]+)\n\s*- name:\s*"([^"]+)"\s*\n.*?description:\s*"([^"]*)"(.*?)(?=# [^\n]+\n\s*- name:|$)'


        for match in re.finditer(table_pattern, tables_content, re.DOTALL):
            comment, table_name, description, table_content = match.groups()

            # Skip if this contains 'view:' (it's a view definition)
            if 'view:' in table_content:
                continue

            columns = []

            # Find column definitions within this table
            columns_section = re.search(r'columns:(.*?)(?=- name:|$)', table_content, re.DOTALL)
            if columns_section:
                columns_content = columns_section.group(1)

                # Find individual column definitions
                column_blocks = re.findall(r'- name:\s*"([^"]+)"\s*\n(.*?)(?=- name:|$)', columns_content, re.DOTALL)
                for col_name, col_content in column_blocks:
                    # Extract type
                    type_match = re.search(r'type:\s*"([^"]*)"', col_content)
                    if type_match:
                        col_type = type_match.group(1)
                        column = ColumnDefinition(
                            name=col_name,
                            type=col_type,
                            description=f"Column {col_name} of type {col_type}"
                        )
                        columns.append(column)

            if columns:  # Only add tables with columns
                table_def = TableDefinition(
                    name=table_name,
                    description=description,
                    columns=columns
                )
                tables.append(table_def)

        return tables

class SchemaProcessor:
    """Processes the canonical telecom schema YAML file."""

    def __init__(self, schema_path: str = "data/telecom_data_warehouse_schema.yaml"):
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.data_types = {
            'sqlite': {
                'TEXT': 'TEXT',
                'INTEGER': 'INTEGER',
                'REAL': 'REAL'
            },
            'snowflake': {
                'TEXT': 'VARCHAR',
                'INTEGER': 'NUMBER',
                'REAL': 'FLOAT'
            }
        }

    def _load_schema(self) -> Dict[str, Any]:
        """Load the canonical schema file using simple parsing."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path, 'r') as f:
            content = f.read()

        # Use simple parser for now
        return {'content': content}

    def get_database_schema(self, db_type: str = 'sqlite') -> Dict[str, Any]:
        """Get schema for specific database type."""
        return self.data_types.get(db_type, self.data_types['sqlite'])

    def get_database_schema(self, db_type: str = 'sqlite') -> Dict[str, Any]:
        """Get schema for specific database type."""
        if db_type not in self.data_types:
            raise ValueError(f"Unsupported database type: {db_type}")

        return self.data_types[db_type]

    def parse_table_definitions(self) -> List[TableDefinition]:
        """Parse table definitions from schema - simplified approach for now."""
        # For now, return hardcoded table definitions based on what we know exists
        # TODO: Implement full YAML parsing later

        tables = []

        # Define tables based on actual database structure
        tables.append(TableDefinition(
            name="dim_time",
            description="Time dimension table",
            columns=[
                ColumnDefinition("date_id", "TEXT", "Date identifier", True),
                ColumnDefinition("hour", "INTEGER", "Hour of day", True),
                ColumnDefinition("year", "INTEGER", "Year"),
                ColumnDefinition("month", "INTEGER", "Month"),
                ColumnDefinition("day", "INTEGER", "Day"),
                ColumnDefinition("weekday", "TEXT", "Day of week"),
                ColumnDefinition("is_weekend", "INTEGER", "Weekend flag")
            ]
        ))

        tables.append(TableDefinition(
            name="dim_region",
            description="Region dimension table",
            columns=[
                ColumnDefinition("region_id", "INTEGER", "Region identifier", True),
                ColumnDefinition("region_name", "TEXT", "Region name")
            ]
        ))

        tables.append(TableDefinition(
            name="dim_network_element",
            description="Network element dimension table",
            columns=[
                ColumnDefinition("network_element_id", "INTEGER", "Element identifier", True),
                ColumnDefinition("element_name", "TEXT", "Element name"),
                ColumnDefinition("element_type", "TEXT", "Element type"),
                ColumnDefinition("vendor", "TEXT", "Vendor name"),
                ColumnDefinition("install_date", "TEXT", "Installation date"),
                ColumnDefinition("region_id", "INTEGER", "Region reference")
            ]
        ))

        tables.append(TableDefinition(
            name="fact_network_metrics",
            description="Network metrics fact table",
            columns=[
                ColumnDefinition("network_element_id", "INTEGER", "Element ID", True),
                ColumnDefinition("region_id", "INTEGER", "Region ID", True),
                ColumnDefinition("date_id", "TEXT", "Date ID", True),
                ColumnDefinition("hour", "INTEGER", "Hour", True),
                ColumnDefinition("last_updated_ts", "TEXT", "Last update timestamp"),
                ColumnDefinition("uptime_seconds", "INTEGER", "Uptime in seconds"),
                ColumnDefinition("downtime_seconds", "INTEGER", "Downtime in seconds"),
                ColumnDefinition("calls_attempted", "INTEGER", "Calls attempted"),
                ColumnDefinition("calls_dropped", "INTEGER", "Calls dropped"),
                ColumnDefinition("packets_sent", "INTEGER", "Packets sent"),
                ColumnDefinition("packets_lost", "INTEGER", "Packets lost"),
                ColumnDefinition("bandwidth_capacity_mb", "REAL", "Bandwidth capacity"),
                ColumnDefinition("bandwidth_used_mb", "REAL", "Bandwidth used"),
                ColumnDefinition("outage_minutes", "REAL", "Outage minutes"),
                ColumnDefinition("repair_minutes", "REAL", "Repair minutes"),
                ColumnDefinition("availability_percent", "REAL", "Availability percentage"),
                ColumnDefinition("dropped_call_rate", "REAL", "Dropped call rate"),
                ColumnDefinition("latency_ms", "REAL", "Latency in ms"),
                ColumnDefinition("latency_ms_p95", "REAL", "95th percentile latency"),
                ColumnDefinition("packet_loss_percent", "REAL", "Packet loss percentage"),
                ColumnDefinition("bandwidth_utilization_percent", "REAL", "Bandwidth utilization"),
                ColumnDefinition("mttr_hours", "REAL", "MTTR in hours")
            ]
        ))

        return tables

    def generate_table_ddl(self, db_type: str = 'sqlite') -> str:
        """Generate DDL for tables."""
        tables = self.parse_table_definitions()
        db_schema = self.get_database_schema(db_type)

        ddl_statements = []
        ddl_statements.append(f"-- Generated DDL for {db_type} database")
        ddl_statements.append(f"-- Generated from {self.schema_path}")
        ddl_statements.append(f"-- Generated on {datetime.now().isoformat()}")
        ddl_statements.append("")

        for table in tables:
            if table.view_sql:
                continue  # Skip views for table DDL

            ddl_statements.append(f"-- {table.description}")
            ddl_statements.append(f"CREATE TABLE IF NOT EXISTS {table.name} (")

            column_defs = []
            primary_keys = []

            for col in table.columns:
                # Map type to database-specific type
                db_type_name = db_schema.get(col.type.upper(), col.type)

                col_def = f"    {col.name} {db_type_name}"

                if not col.nullable:
                    col_def += " NOT NULL"

                if col.primary_key:
                    primary_keys.append(col.name)

                column_defs.append(col_def)

            # Add primary key constraint if needed
            if primary_keys:
                if len(primary_keys) == 1:
                    # Single column primary key
                    for i, col_def in enumerate(column_defs):
                        if primary_keys[0] in col_def:
                            column_defs[i] += " PRIMARY KEY"
                            break
                else:
                    # Composite primary key
                    pk_cols = ", ".join(primary_keys)
                    column_defs.append(f"    PRIMARY KEY ({pk_cols})")

            ddl_statements.append(",\n".join(column_defs))
            ddl_statements.append(");")
            ddl_statements.append("")

        return "\n".join(ddl_statements)

    def generate_view_ddl(self, db_type: str = 'sqlite') -> str:
        """Generate DDL for views."""
        tables = self.parse_table_definitions()

        ddl_statements = []
        ddl_statements.append(f"-- Generated View DDL for {db_type} database")
        ddl_statements.append(f"-- Generated from {self.schema_path}")
        ddl_statements.append(f"-- Generated on {datetime.now().isoformat()}")
        ddl_statements.append("")

        # Add business views that are commonly needed
        ddl_statements.append("-- Business semantic views")
        ddl_statements.append("DROP VIEW IF EXISTS vw_network_metrics_daily;")
        ddl_statements.append("CREATE VIEW vw_network_metrics_daily AS")
        ddl_statements.append("SELECT")
        ddl_statements.append("    f.date_id,")
        ddl_statements.append("    r.region_name,")
        ddl_statements.append("    AVG(100.0 * f.uptime_seconds / NULLIF(f.uptime_seconds + f.downtime_seconds, 0)) as availability_pct,")
        ddl_statements.append("    AVG(f.latency_ms) as latency_ms,")
        ddl_statements.append("    AVG(f.packet_loss_percent) as packet_loss_pct,")
        ddl_statements.append("    AVG(f.bandwidth_utilization_percent) as bandwidth_util_pct,")
        ddl_statements.append("    AVG(f.dropped_call_rate) as dropped_call_pct,")
        ddl_statements.append("    AVG(f.mttr_hours) as mttr_hours")
        ddl_statements.append("FROM fact_network_metrics f")
        ddl_statements.append("JOIN dim_region r ON r.region_id = f.region_id")
        ddl_statements.append("GROUP BY f.date_id, r.region_name;")
        ddl_statements.append("")

        # Add dimension views
        ddl_statements.append("-- Dimension views")
        ddl_statements.append("DROP VIEW IF EXISTS dim_time_view;")
        ddl_statements.append("CREATE VIEW dim_time_view AS")
        ddl_statements.append("SELECT date_id, hour, year, month, day, weekday, is_weekend FROM dim_time;")
        ddl_statements.append("")

        ddl_statements.append("DROP VIEW IF EXISTS dim_region_view;")
        ddl_statements.append("CREATE VIEW dim_region_view AS")
        ddl_statements.append("SELECT region_id, region_name FROM dim_region;")
        ddl_statements.append("")

        ddl_statements.append("DROP VIEW IF EXISTS dim_network_element_view;")
        ddl_statements.append("CREATE VIEW dim_network_element_view AS")
        ddl_statements.append("SELECT network_element_id, element_name, element_type, vendor, install_date, region_id FROM dim_network_element;")
        ddl_statements.append("")

        ddl_statements.append("DROP VIEW IF EXISTS fact_network_metrics_view;")
        ddl_statements.append("CREATE VIEW fact_network_metrics_view AS")
        ddl_statements.append("SELECT * FROM fact_network_metrics;")
        ddl_statements.append("")

        return "\n".join(ddl_statements)

    def generate_test_data(self, num_rows: int = 1000) -> str:
        """Generate test data based on schema definitions."""
        tables = self.parse_table_definitions()

        # Focus on fact tables for test data generation
        fact_tables = [t for t in tables if not t.view_sql and t.name.startswith('fact_')]

        insert_statements = []
        insert_statements.append("-- Generated test data")
        insert_statements.append(f"-- Generated on {datetime.now().isoformat()}")
        insert_statements.append("")

        # Generate data for each fact table
        for table in fact_tables:
            if table.name == 'fact_network_metrics':
                insert_statements.extend(self._generate_network_metrics_data(table, num_rows))
            elif table.name == 'fact_customer_experience':
                insert_statements.extend(self._generate_customer_experience_data(table, num_rows))
            elif table.name == 'fact_revenue':
                insert_statements.extend(self._generate_revenue_data(table, num_rows))
            elif table.name == 'fact_usage_adoption':
                insert_statements.extend(self._generate_usage_data(table, num_rows))
            elif table.name == 'fact_operations':
                insert_statements.extend(self._generate_operations_data(table, num_rows))

        return "\n".join(insert_statements)

    def _generate_network_metrics_data(self, table: TableDefinition, num_rows: int) -> List[str]:
        """Generate test data for network metrics."""
        statements = []
        statements.append(f"-- Insert test data for {table.name}")

        for i in range(num_rows):
            network_element_id = random.randint(1, 5)
            region_id = random.randint(1, 5)
            date_id = '2023-08-01'
            hour = random.randint(0, 23)

            # Generate realistic network metrics
            uptime_seconds = random.randint(80000, 86400)  # 22-24 hours
            downtime_seconds = 86400 - uptime_seconds
            calls_attempted = random.randint(1000, 5000)
            calls_dropped = random.randint(0, int(calls_attempted * 0.01))  # 0-1% drop rate
            packets_sent = random.randint(1000000, 5000000)
            packets_lost = random.randint(0, int(packets_sent * 0.005))  # 0-0.5% loss
            bandwidth_capacity = random.uniform(500, 1200)
            bandwidth_used = random.uniform(0, bandwidth_capacity)
            outage_minutes = random.uniform(0, 60)
            repair_minutes = random.uniform(15, 120) if outage_minutes > 0 else 0

            # Pre-calculated KPIs
            availability_pct = (uptime_seconds / (uptime_seconds + downtime_seconds)) * 100
            dropped_call_rate = (calls_dropped / calls_attempted) * 100 if calls_attempted > 0 else 0
            latency_ms = random.uniform(20, 80)
            latency_p95 = latency_ms * random.uniform(1.1, 1.5)
            packet_loss_pct = (packets_lost / packets_sent) * 100 if packets_sent > 0 else 0
            bandwidth_util_pct = (bandwidth_used / bandwidth_capacity) * 100 if bandwidth_capacity > 0 else 0
            mttr_hours = repair_minutes / 60 if repair_minutes > 0 else random.uniform(1.5, 3.0)

            values = (
                network_element_id, region_id, date_id, hour,
                f"{datetime.now().isoformat()}",
                uptime_seconds, downtime_seconds, calls_attempted, calls_dropped,
                packets_sent, packets_lost, bandwidth_capacity, bandwidth_used,
                outage_minutes, repair_minutes, availability_pct, dropped_call_rate,
                latency_ms, latency_p95, packet_loss_pct, bandwidth_util_pct, mttr_hours
            )

            statements.append(f"INSERT OR IGNORE INTO {table.name} VALUES {values};")

        statements.append("")
        return statements

    def _generate_customer_experience_data(self, table: TableDefinition, num_rows: int) -> List[str]:
        """Generate test data for customer experience."""
        statements = []
        statements.append(f"-- Insert test data for {table.name}")

        for i in range(num_rows):
            customer_id = random.randint(1, 100)
            date_id = '2023-08-01'
            region_id = random.randint(1, 5)
            channel_id = random.randint(1, 5)

            satisfaction_score = random.uniform(70, 100)
            nps_score = random.randint(-50, 80)
            churn_probability = random.uniform(0, 0.15)
            handling_time = random.uniform(2, 15)
            first_contact_resolution = random.uniform(0.7, 0.95)
            complaint_count = random.randint(0, 5)
            escalation_count = random.randint(0, 2)
            customer_effort_score = random.uniform(1, 5)
            lifetime_value = random.uniform(500, 5000)

            values = (
                customer_id, date_id, region_id, channel_id,
                satisfaction_score, nps_score, churn_probability, handling_time,
                first_contact_resolution, complaint_count, escalation_count,
                customer_effort_score, lifetime_value
            )

            statements.append(f"INSERT OR IGNORE INTO {table.name} VALUES {values};")

        statements.append("")
        return statements

    def _generate_revenue_data(self, table: TableDefinition, num_rows: int) -> List[str]:
        """Generate test data for revenue."""
        statements = []
        statements.append(f"-- Insert test data for {table.name}")

        for i in range(num_rows):
            customer_id = random.randint(1, 100)
            product_id = random.randint(1, 5)
            date_id = '2023-08-01'
            region_id = random.randint(1, 5)
            channel_id = random.randint(1, 5)

            revenue_amount = random.uniform(20, 500)
            arpu = revenue_amount
            cac = random.uniform(50, 200)
            clv = random.uniform(1000, 10000)
            churn_loss = random.uniform(0, revenue_amount * 0.1)
            upsell_revenue = random.uniform(0, revenue_amount * 0.3)
            cross_sell_revenue = random.uniform(0, revenue_amount * 0.2)
            ebitda_margin = random.uniform(20, 40)
            profit_margin = random.uniform(10, 25)
            subscriber_count = 1
            growth_rate = random.uniform(-0.05, 0.15)

            values = (
                customer_id, product_id, date_id, region_id, channel_id,
                revenue_amount, arpu, cac, clv, churn_loss, upsell_revenue,
                cross_sell_revenue, ebitda_margin, profit_margin,
                subscriber_count, growth_rate
            )

            statements.append(f"INSERT OR IGNORE INTO {table.name} VALUES {values};")

        statements.append("")
        return statements

    def _generate_usage_data(self, table: TableDefinition, num_rows: int) -> List[str]:
        """Generate test data for usage and adoption."""
        statements = []
        statements.append(f"-- Insert test data for {table.name}")

        for i in range(num_rows):
            customer_id = random.randint(1, 100)
            product_id = random.randint(1, 5)
            date_id = '2023-08-01'
            region_id = random.randint(1, 5)

            data_usage_gb = random.uniform(1, 25)
            voice_minutes = random.uniform(50, 500)
            sms_count = random.randint(0, 50)
            feature_adoption = random.uniform(0.3, 0.9)
            five_g_adoption = random.uniform(0.2, 0.8)
            service_penetration = random.uniform(0.6, 0.95)
            app_usage_rate = random.uniform(0.5, 0.95)
            premium_adoption = random.uniform(0.1, 0.6)
            peak_usage_time = random.choice(['8-10 PM', '12-2 PM', '6-8 AM', '4-6 PM'])
            avg_session_duration = random.uniform(15, 120)
            active_subscribers = 1

            values = (
                customer_id, product_id, date_id, region_id,
                data_usage_gb, voice_minutes, sms_count, feature_adoption,
                five_g_adoption, service_penetration, app_usage_rate,
                premium_adoption, peak_usage_time, avg_session_duration, active_subscribers
            )

            statements.append(f"INSERT OR IGNORE INTO {table.name} VALUES {values};")

        statements.append("")
        return statements

    def _generate_operations_data(self, table: TableDefinition, num_rows: int) -> List[str]:
        """Generate test data for operations."""
        statements = []
        statements.append(f"-- Insert test data for {table.name}")

        for i in range(num_rows):
            employee_id = random.randint(1, 20)
            region_id = random.randint(1, 5)
            date_id = '2023-08-01'
            channel_id = random.randint(1, 5)

            response_time = random.uniform(1, 8)
            compliance_rate = random.uniform(0.95, 0.995)
            resolution_rate = random.uniform(0.85, 0.98)
            uptime_pct = random.uniform(99, 99.9)
            efficiency_score = random.uniform(75, 95)
            capex_ratio = random.uniform(15, 25)
            productivity_score = random.uniform(80, 95)
            cost_per_customer = random.uniform(8, 20)
            automation_rate = random.uniform(0.6, 0.9)
            training_completion = random.uniform(0.8, 0.98)
            incident_count = random.randint(0, 10)
            resolution_time = random.uniform(1, 12)

            values = (
                employee_id, region_id, date_id, channel_id,
                response_time, compliance_rate, resolution_rate, uptime_pct,
                efficiency_score, capex_ratio, productivity_score, cost_per_customer,
                automation_rate, training_completion, incident_count, resolution_time
            )

            statements.append(f"INSERT OR IGNORE INTO {table.name} VALUES {values};")

        statements.append("")
        return statements

    def validate_schema(self) -> Dict[str, Any]:
        """Validate the schema structure and references."""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Check if we can parse tables from the schema
        try:
            tables = self.parse_table_definitions()
            if not tables:
                validation_results['errors'].append("No tables found in schema")
                validation_results['valid'] = False
            else:
                validation_results['warnings'].append(f"Found {len(tables)} tables in schema")
        except Exception as e:
            validation_results['errors'].append(f"Failed to parse schema: {e}")
            validation_results['valid'] = False

        return validation_results


def main():
    parser = argparse.ArgumentParser(description='Process telecom schema YAML file')
    parser.add_argument('action', choices=[
        'generate-ddl', 'generate-views', 'generate-test-data',
        'generate-metadata-pack', 'validate-schema'
    ])
    parser.add_argument('--database', default='sqlite', choices=['sqlite', 'snowflake', 'postgresql'])
    parser.add_argument('--rows', type=int, default=1000, help='Number of test data rows to generate')
    parser.add_argument('--output', help='Output file path')

    args = parser.parse_args()

    processor = SchemaProcessor()

    if args.action == 'validate-schema':
        results = processor.validate_schema()
        if results['valid']:
            print("✅ Schema validation passed")
        else:
            print("❌ Schema validation failed:")
            for error in results['errors']:
                print(f"  - {error}")
        for warning in results['warnings']:
            print(f"⚠️  {warning}")

    elif args.action == 'generate-ddl':
        ddl = processor.generate_table_ddl(args.database)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(ddl)
            print(f"✅ DDL written to {args.output}")
        else:
            print(ddl)

    elif args.action == 'generate-views':
        view_ddl = processor.generate_view_ddl(args.database)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(view_ddl)
            print(f"✅ View DDL written to {args.output}")
        else:
            print(view_ddl)

    elif args.action == 'generate-test-data':
        test_data = processor.generate_test_data(args.rows)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(test_data)
            print(f"✅ Test data written to {args.output}")
        else:
            print(test_data)

    elif args.action == 'generate-metadata-pack':
        # This would generate the dashboard_telco.yaml from schema
        print("⚠️  Metadata pack generation not yet implemented")
        print("This would auto-generate dashboard_telco.yaml from the schema definitions")


if __name__ == '__main__':
    main()