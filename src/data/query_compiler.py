"""Query compiler that renders metadata SQL templates with filters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, Mapping, Optional
from zoneinfo import ZoneInfo

from jinja2 import Environment

from metadata_runtime.dialects import MacroRegistry, MacroRegistryError
from metadata_runtime.models import KpiMetricConfig, MetadataConfig


@dataclass(frozen=True)
class CompiledQuery:
    sql: str
    data_source_id: str
    dialect: str
    params: Dict[str, Any]
    fallback_source_id: Optional[str] = None


class QueryCompilerError(RuntimeError):
    """Raised when SQL compilation fails."""


def _quote(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _csv(values: Any) -> str:
    if values is None:
        return "NULL"
    if not isinstance(values, (list, tuple, set)):
        values = [values]
    return ", ".join(_quote(value) for value in values)


def _freeze(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return SimpleNamespace(**{key: _freeze(value) for key, value in obj.items()})
    if isinstance(obj, list):
        return [_freeze(item) for item in obj]
    return obj


def _literal(value: Any) -> str:
    if value is None:
        return "NULL"
    text = str(value)
    if text.startswith("'") and text.endswith("'"):
        return text
    return _quote(text)


class QueryCompiler:
    """Render metric SQL templates with filter bindings and macros."""

    def __init__(
        self,
        config: MetadataConfig,
        macro_registry: MacroRegistry | None = None,
    ) -> None:
        self._config = config
        self._macro_registry = macro_registry
        self._metric_index: Dict[str, KpiMetricConfig] = {}
        for kpi in config.kpis:
            for metric in kpi.metrics:
                self._metric_index[metric.id] = metric
        for metric in config.auxiliary_metrics:
            self._metric_index[metric.id] = metric
        self._timezone = config.globals.timezone

    def compile(self, metric_id: str, filters: Optional[Mapping[str, Any]] = None) -> CompiledQuery:
        metric = self._metric_index.get(metric_id)
        if metric is None:
            raise QueryCompilerError(f"Metric '{metric_id}' not defined in metadata")

        data_source_id = metric.data_source
        data_source = self._config.data_sources.get(data_source_id)
        if data_source is None:
            raise QueryCompilerError(f"Data source '{data_source_id}' not defined")
        dialect = getattr(metric, "dialect", None) or data_source.dialect

        rendered_sql = self._render_sql(metric, dialect, filters or {})
        return CompiledQuery(
            sql=rendered_sql.strip(),
            data_source_id=data_source_id,
            dialect=dialect,
            params={},
            fallback_source_id=getattr(metric, "fallback_source", None),
        )

    def _render_sql(
        self,
        metric: KpiMetricConfig,
        dialect: str,
        filters: Mapping[str, Any],
    ) -> str:
        env = Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
        env.filters["quote"] = _quote
        env.filters["csv"] = _csv

        if self._macro_registry:
            try:
                namespace = self._macro_registry.get_namespace(dialect)
            except MacroRegistryError:
                namespace = {}
            env.globals.update(namespace)

        template = env.from_string(metric.sql)
        render_context = {
            "filters": filters,
            "date_range": self._resolve_date_range(filters.get("date_range")),
        }
        frozen_context = {key: _freeze(value) for key, value in render_context.items()}
        rendered_sql = template.render(**frozen_context)
        return rendered_sql

    def _resolve_date_range(self, value: Any) -> Dict[str, str]:
        timezone = None
        if self._timezone:
            try:
                timezone = ZoneInfo(self._timezone)
            except Exception:
                timezone = None
        today = datetime.now(tz=timezone).date() if timezone else date.today()

        if isinstance(value, Mapping):
            start = value.get("start")
            end = value.get("end")
            return {"start": _literal(start), "end": _literal(end)}

        if isinstance(value, (list, tuple)) and len(value) == 2:
            start, end = value
            return {"start": _literal(start), "end": _literal(end)}

        alias = str(value or self._config.globals.default_date_range).lower()
        if alias == "last_7_days":
            start = today - timedelta(days=6)
            end = today
        elif alias == "last_30_days":
            start = today - timedelta(days=29)
            end = today
        elif alias == "last_12_months":
            start = today - timedelta(days=365)
            end = today
        elif alias == "qtd":
            month = ((today.month - 1) // 3) * 3 + 1
            start = today.replace(month=month, day=1)
            end = today
        elif alias == "ytd":
            start = today.replace(month=1, day=1)
            end = today
        else:
            start = today - timedelta(days=29)
            end = today
        return {"start": _literal(start.isoformat()), "end": _literal(end.isoformat())}


__all__ = ["QueryCompiler", "QueryCompilerError", "CompiledQuery"]
