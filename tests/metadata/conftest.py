from __future__ import annotations

from typing import Dict

import pytest


def _base_metadata_dict() -> Dict:
    return {
        "schema_version": "1.0",
        "app_version": "0.9.0",
        "pack_id": "test_pack",
        "label": "Test Pack",
        "globals": {
            "timezone": "America/Chicago",
            "default_date_range": "last_30_days",
            "ai_insights_enabled": True,
            "print_mode_enabled": False,
        },
        "dialects": {
            "default": "snowflake",
            "supported": ["snowflake", "sqlite"],
        },
        "data_sources": {
            "snowflake_main": {
                "dialect": "snowflake",
                "dsn_env": "SNOWFLAKE_DSN",
                "role": "ANALYST",
                "warehouse": "KPI_WH",
                "database": "TELECOM",
                "schema": "ANALYTICS",
            },
            "sqlite_cache": {
                "dialect": "sqlite",
                "path": "./data/cache.db",
                "read_only": True,
            },
        },
        "filters": {
            "global": [
                {
                    "id": "date_range",
                    "type": "date_range",
                    "label": "Date Range",
                    "default": "last_30_days",
                    "bindings": {"start_param": "start_date", "end_param": "end_date"},
                }
            ],
            "subject_area": {},
        },
        "subject_areas": [
            {
                "id": "network",
                "title": "Network",
                "layout": {
                    "grid_columns": 12,
                    "sections": [
                        {
                            "id": "cards",
                            "rows": [[{"kpi_card": "kpi_network_availability"}]],
                        }
                    ],
                },
            }
        ],
        "kpis": [
            {
                "id": "kpi_network_availability",
                "title": "Network Availability",
                "subject_area": "network",
                "metrics": [
                    {
                        "id": "metric_network_availability",
                        "data_source": "snowflake_main",
                        "sql": "SELECT 1",
                    }
                ],
                "widgets": {
                    "primary": {
                        "type": "kpi_card",
                        "dataset": "metric_network_availability",
                    },
                    "secondary": [],
                },
            }
        ],
        "auxiliary_metrics": [],
    }


@pytest.fixture
def metadata_dict() -> Dict:
    return _base_metadata_dict()
