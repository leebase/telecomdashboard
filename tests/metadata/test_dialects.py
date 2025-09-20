from pathlib import Path

import pytest

from metadata_runtime.dialects import MacroRegistry, MacroRegistryError


def _load_registry() -> MacroRegistry:
    registry = MacroRegistry()
    repo_root = Path(__file__).resolve().parents[2]
    macros_dir = repo_root / "src" / "metadata_runtime" / "dialects" / "macros"
    registry.load_from_file("snowflake", macros_dir / "snowflake.sql")
    registry.load_from_file("sqlite", macros_dir / "sqlite.sql")
    return registry


def test_macro_registry_loads_macros():
    registry = _load_registry()

    snowflake_ns = registry.get_namespace("snowflake")
    assert "date_trunc" in snowflake_ns
    assert "apply_limit" in snowflake_ns

    sqlite_ns = registry.get_namespace("sqlite")
    assert "qualify" in sqlite_ns


def test_macro_resolution_errors():
    registry = MacroRegistry()
    with pytest.raises(MacroRegistryError):
        registry.resolve("snowflake", "date_trunc")


@pytest.mark.parametrize(
    "dialect,expected",
    [
        ("snowflake", "DATE_TRUNC('DAY', created_at)"),
        (
            "sqlite",
            "CASE 'day'\n  WHEN 'day' THEN DATE(created_at)\n  WHEN 'week' THEN DATE(created_at, 'weekday 0', '-6 days')\n  WHEN 'month' THEN DATE(created_at, 'start of month')\n  WHEN 'quarter' THEN DATE(created_at, 'start of month', ((CAST(STRFTIME('%m', created_at) AS INTEGER) - 1) / 3) * -1 || ' months')\n  WHEN 'year' THEN DATE(created_at, 'start of year')\n  ELSE DATE(created_at)\nEND",
        ),
    ],
)
def test_date_trunc_macro_renders(dialect, expected):
    registry = _load_registry()
    macro = registry.resolve(dialect, "date_trunc")
    result = macro("day", "created_at")
    assert result.strip() == expected.strip()
