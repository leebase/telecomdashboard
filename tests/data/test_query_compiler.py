from pathlib import Path

from data.query_compiler import QueryCompiler
from metadata_runtime.dialects import MacroRegistry
from metadata_runtime.loader import load_metadata


def test_query_compiler_renders_sql_with_filters(tmp_path):
    metadata_path = Path("metadata/dashboard_telco.yaml").resolve()
    config = load_metadata(metadata_path)
    registry = MacroRegistry()
    macros = config.dialects.macros
    base_dir = metadata_path.parent
    if macros:
        if macros.snowflake:
            registry.load_from_file("snowflake", base_dir / macros.snowflake)
        if macros.sqlite:
            registry.load_from_file("sqlite", base_dir / macros.sqlite)

    compiler = QueryCompiler(config, registry)
    compiled = compiler.compile(
        "metric_network_latency",
        filters={"region": "Northeast", "date_range": "last_7_days"},
    )

    assert "Northeast" in compiled.sql
    assert "BETWEEN" in compiled.sql
    assert compiled.data_source_id == "sqlite_cache"
    assert compiled.dialect == "sqlite"


def test_query_compiler_handles_auxiliary_metrics():
    metadata_path = Path("metadata/dashboard_telco.yaml").resolve()
    config = load_metadata(metadata_path)

    compiler = QueryCompiler(config)
    compiled = compiler.compile("metric_financial_summary")

    assert "SELECT 'Total Revenue'" in compiled.sql
    assert compiled.data_source_id == "sqlite_cache"
    assert compiled.dialect == "sqlite"
