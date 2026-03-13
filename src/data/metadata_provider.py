"""Metadata-driven data provider that fetches metric data via datasources."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

from data.cache import TTLCache, get_cache
from data.datasource import DataSourceError, DataSourceFactory
from data.query_compiler import CompiledQuery, QueryCompiler, QueryCompilerError
from metadata_runtime.dialects import MacroRegistry
from metadata_runtime.models import (
    FilterConfig,
    KpiConfig,
    KpiMetricConfig,
    MetadataConfig,
    SecondaryWidgetConfig,
    WidgetRegistryOverride,
)

logger = logging.getLogger(__name__)

_EXPRESSION_RE = re.compile(r"^(?P<func>[a-zA-Z_][a-zA-Z0-9_]*)\((?P<arg>[a-zA-Z_][a-zA-Z0-9_]*)\)$")
_REGIONS = ["North", "South", "East", "West"]


def _normalize_filter_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple((k, _normalize_filter_value(v)) for k, v in sorted(value.items()))
    if isinstance(value, list):
        return tuple(_normalize_filter_value(item) for item in value)
    return value


def _freeze_filters(filters: Mapping[str, Any]) -> Tuple[Tuple[str, Any], ...]:
    frozen: list[Tuple[str, Any]] = []
    for key in sorted(filters.keys()):
        frozen.append((key, _normalize_filter_value(filters[key])))
    return tuple(frozen)


@dataclass(frozen=True)
class MetricContext:
    metric: KpiMetricConfig
    filters: Dict[str, Any]


class MetadataDataProvider:
    """Resolves metric datasets for metadata-driven widgets."""

    def __init__(self, config: MetadataConfig, metadata_path: Path) -> None:
        self._config = config
        self._metadata_path = metadata_path.resolve()

        self._macro_registry = MacroRegistry()
        self._load_macros()

        self._compiler = QueryCompiler(config, self._macro_registry)
        self._factory = DataSourceFactory(config, self._metadata_path)

        # Initialize TTL cache
        default_ttl = config.refresh.default_ttl_seconds if config.refresh else 300
        sqlite_path = None
        # Check if SQLite datasource exists for cache
        for ds_config in config.data_sources.values():
            if ds_config.dialect == "sqlite" and ds_config.path:
                sqlite_path = Path(ds_config.path).parent / "cache.db"
                break
        self._cache = get_cache(default_ttl=default_ttl, sqlite_path=sqlite_path)

        self._metric_index: Dict[str, KpiMetricConfig] = {}
        self._metric_subject_area: Dict[str, str] = {}
        for kpi in config.kpis:
            for metric in kpi.metrics:
                self._metric_index[metric.id] = metric
                self._metric_subject_area[metric.id] = kpi.subject_area
        for metric in config.auxiliary_metrics:
            self._metric_index[metric.id] = metric

        self._kpi_index: Dict[str, KpiConfig] = {kpi.id: kpi for kpi in config.kpis}
        self._subject_index = {area.id: area for area in config.subject_areas}

        self._global_filters = {flt.id: flt for flt in config.filters.global_}
        self._subject_filters: Dict[str, Dict[str, FilterConfig]] = {}
        for subject_id, filters in config.filters.subject_area.items():
            self._subject_filters[subject_id] = {flt.id: flt for flt in filters}

        self._rng_cache: Dict[str, np.random.Generator] = {}

    def _load_macros(self) -> None:
        macros = self._config.dialects.macros
        if not macros:
            return
        base_dir = self._metadata_path.parent
        if macros.snowflake:
            try:
                self._macro_registry.load_from_file("snowflake", (base_dir / macros.snowflake).resolve())
            except FileNotFoundError as exc:
                logger.warning("Snowflake macro file missing: %s", exc)
        if macros.sqlite:
            try:
                self._macro_registry.load_from_file("sqlite", (base_dir / macros.sqlite).resolve())
            except FileNotFoundError as exc:
                logger.warning("SQLite macro file missing: %s", exc)

    def _seed_rng(self, metric_id: str) -> np.random.Generator:
        if metric_id not in self._rng_cache:
            seed = abs(hash(metric_id)) % 10_000
            self._rng_cache[metric_id] = np.random.default_rng(seed)
        return self._rng_cache[metric_id]

    def _resolve_default_filters(self, subject_area_id: str) -> Dict[str, Any]:
        context: Dict[str, Any] = {}
        subject = self._subject_index.get(subject_area_id)
        if subject is None:
            return context
        for filter_id in subject.default_filters:
            filter_cfg = self._lookup_filter(filter_id, subject_area_id)
            if filter_cfg is None:
                continue
            if filter_cfg.default is not None:
                context[filter_id] = filter_cfg.default
            else:
                context[filter_id] = None
        return context

    def _lookup_filter(self, filter_id: str, subject_area_id: str) -> Optional[FilterConfig]:
        if filter_id in self._global_filters:
            return self._global_filters[filter_id]
        subject_filters = self._subject_filters.get(subject_area_id, {})
        return subject_filters.get(filter_id)

    def get_metric_frame(self, metric_id: str, filters: Optional[Mapping[str, Any]] = None) -> pd.DataFrame:
        filters = filters or {}
        cache_key = f"{metric_id}:{_freeze_filters(filters)}"

        # Try cache first
        cached_frame = self._cache.get(cache_key)
        if cached_frame is not None:
            return cached_frame

        metric = self._metric_index.get(metric_id)
        if not metric:
            raise KeyError(f"Metric '{metric_id}' not found")

        try:
            compiled = self._compiler.compile(metric_id, filters)
            frame = self._execute_query(compiled)
        except (QueryCompilerError, DataSourceError) as exc:
            logger.warning("Falling back to stub data for metric %s due to error: %s", metric_id, exc)
            frame = self._build_stub_frame(metric)

        if frame.empty:
            frame = self._build_stub_frame(metric)

        # Cache with metric-specific TTL
        ttl = metric.cache_ttl_seconds
        if ttl is None and self._config.refresh:
            # Check for overrides
            if self._config.refresh.overrides and metric_id in self._config.refresh.overrides.__root__:
                ttl = self._config.refresh.overrides.__root__[metric_id]
            else:
                ttl = self._config.refresh.default_ttl_seconds

        self._cache.put(cache_key, frame, ttl)
        return frame

    def _execute_query(self, compiled: CompiledQuery) -> pd.DataFrame:
        datasource = self._factory.get(compiled.data_source_id)
        try:
            frame = datasource.execute(compiled.sql, compiled.params)
        except DataSourceError:
            if compiled.fallback_source_id:
                logger.info(
                    "Primary datasource '%s' failed; attempting fallback '%s'",
                    compiled.data_source_id,
                    compiled.fallback_source_id,
                )
                fallback_ds = self._factory.get(compiled.fallback_source_id)
                return fallback_ds.execute(compiled.sql, compiled.params)
            raise
        return frame

    def build_kpi_payload(self, kpi: KpiConfig) -> Dict[str, Any]:
        return self.build_kpi_payload_for_filters(kpi)

    def build_kpi_payload_for_filters(
        self,
        kpi: KpiConfig,
        runtime_filters: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        primary = kpi.widgets.primary
        filters = self._merge_filters(self._resolve_default_filters(kpi.subject_area), runtime_filters)
        frame = self.get_metric_frame(primary.dataset, filters)
        primary_metric = next((metric for metric in kpi.metrics if metric.id == primary.dataset), None)
        if primary_metric is not None:
            frame = self._normalize_kpi_frame(frame, primary_metric)
        value = self._evaluate_expression(frame, primary.value_expr)
        delta = self._evaluate_expression(frame, primary.delta_expr)
        decimals = primary.decimals if primary.decimals is not None else 2
        if value is not None:
            value = round(float(value), decimals)
        if delta is not None:
            delta = round(float(delta), decimals)
        return {
            "label": kpi.title,
            "value": value,
            "delta": delta,
            "unit": primary.unit or "",
            "tooltip": kpi.description or "",
        }

    def build_chart_payload(
        self,
        kpi: KpiConfig,
        chart: SecondaryWidgetConfig,
        runtime_filters: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        filters = self._merge_filters(self._resolve_default_filters(kpi.subject_area), runtime_filters)
        frame = self.get_metric_frame(chart.dataset, filters)
        transformed = self._transform_chart_frame(frame, chart)
        title = chart.encoding.get("title") if chart.encoding else None
        return {
            "title": title or kpi.title,
            "y_label": kpi.widgets.primary.unit or "Value",
            "dataframe": transformed,
            "encoding": chart.encoding or {},
        }

    def build_widget_payload(
        self,
        widget: WidgetRegistryOverride,
        title: Optional[str] = None,
        runtime_filters: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        filters = self._merge_filters(self._resolve_filters_for_dataset(widget.dataset), runtime_filters)
        frame = self.get_metric_frame(widget.dataset, filters)

        if widget.columns:
            selected_columns = [column for column in widget.columns if column in frame.columns]
            if selected_columns:
                frame = frame[selected_columns]

        return {
            "title": title,
            "dataset": widget.dataset,
            "dataframe": frame,
            "encoding": widget.encoding or {},
            "columns": widget.columns or [],
        }

    def _resolve_filters_for_dataset(self, dataset_id: str) -> Dict[str, Any]:
        subject_area_id = self._metric_subject_area.get(dataset_id)
        if not subject_area_id:
            return {}
        return self._resolve_default_filters(subject_area_id)

    @staticmethod
    def _merge_filters(defaults: Mapping[str, Any], overrides: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        merged = dict(defaults)
        if not overrides:
            return merged
        for key, value in overrides.items():
            merged[key] = value
        return merged

    def _evaluate_expression(self, frame: pd.DataFrame, expression: Optional[str]) -> Optional[float]:
        if frame.empty:
            return None
        if not expression:
            numeric_cols = frame.select_dtypes(include=["number"]).columns
            if not numeric_cols.empty:
                return float(frame[numeric_cols[0]].iloc[-1])
            return None
        match = _EXPRESSION_RE.match(expression.strip())
        if not match:
            if expression in frame.columns:
                return float(frame[expression].iloc[-1])
            return None
        func = match.group("func").lower()
        column = match.group("arg")
        if column not in frame.columns:
            return None
        series = frame[column].dropna()
        if series.empty:
            return None
        if func == "last_value":
            return float(series.iloc[-1])
        if func == "delta":
            if len(series) < 2:
                return 0.0
            return float(series.iloc[-1] - series.iloc[-2])
        if func == "percent_delta":
            if len(series) < 2:
                return 0.0
            previous = series.iloc[-2]
            if previous == 0:
                return 0.0
            return float((series.iloc[-1] - previous) / abs(previous) * 100)
        if func == "weighted_avg":
            return float(series.mean())
        return None

    def _normalize_kpi_frame(self, frame: pd.DataFrame, metric: KpiMetricConfig) -> pd.DataFrame:
        dimensions = list(getattr(metric, "dimensions", []) or [])
        if "date" in dimensions and "date" in frame.columns and frame["date"].duplicated().any():
            numeric_columns = frame.select_dtypes(include=["number"]).columns.tolist()
            if not numeric_columns:
                return frame
            return frame.groupby("date", as_index=False)[numeric_columns].mean()
        return frame

    def _transform_chart_frame(self, frame: pd.DataFrame, chart: SecondaryWidgetConfig) -> pd.DataFrame:
        encoding = chart.encoding or {}
        data = frame.copy()
        if chart.type in {"timeseries_line", "area_chart"}:
            x_col = encoding.get("x", "date")
            y_col = encoding.get("y") or encoding.get("value")
            if x_col not in data.columns or (y_col and y_col not in data.columns):
                return data
            rename_map = {}
            if x_col != "date":
                rename_map[x_col] = "date"
            if y_col and y_col != "value":
                rename_map[y_col] = "value"
            data = data[[x_col, y_col]].rename(columns=rename_map)
            data = data.sort_values("date")
            if data["date"].duplicated().any():
                data = data.groupby("date", as_index=False)["value"].mean()
        elif chart.type == "bar_chart":
            x_col = encoding.get("x")
            y_col = encoding.get("y")
            if not x_col or not y_col or x_col not in data.columns or y_col not in data.columns:
                return data
            rename_map = {}
            if x_col != "category":
                rename_map[x_col] = "category"
            if y_col != "value":
                rename_map[y_col] = "value"
            data = data[[x_col, y_col]].rename(columns=rename_map)
            data = data.groupby("category", as_index=False)["value"].mean()
        return data

    def _build_stub_frame(self, metric: KpiMetricConfig) -> pd.DataFrame:
        rng = self._seed_rng(metric.id)
        aliases = self._extract_aliases(metric.sql)
        if not aliases:
            aliases = ["value"]
        dimensions = list(getattr(metric, "dimensions", []) or [])

        rows = []
        dates = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=14)
        regions = _REGIONS if "region" in dimensions else [None]

        if "date" in dimensions:
            for dt in dates:
                for region in regions:
                    row = {"date": dt}
                    if region is not None:
                        row["region"] = region
                    for alias in aliases:
                        base = rng.uniform(20, 100)
                        jitter = rng.normal(0, 3)
                        row[alias] = round(base + jitter, 2)
                    rows.append(row)
        else:
            categories = regions if any(regions) else [f"cat_{i}" for i in range(len(aliases))]
            for category in categories:
                row: Dict[str, Any] = {}
                if category is not None:
                    row["region" if "region" in dimensions else "category"] = category
                for alias in aliases:
                    row[alias] = round(rng.uniform(20, 100), 2)
                rows.append(row)

        frame = pd.DataFrame(rows)
        return frame

    @staticmethod
    def _extract_aliases(sql: str) -> list[str]:
        return re.findall(r"AS\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, flags=re.IGNORECASE)

    def clear_cache(self) -> int:
        """Clear all cached metric frames."""
        return self._cache.clear()

    def invalidate_metric_cache(self, metric_id: str, filters: Optional[Mapping[str, Any]] = None) -> bool:
        """Invalidate cache for specific metric and filters."""
        filters = filters or {}
        cache_key = f"{metric_id}:{_freeze_filters(filters)}"
        return self._cache.invalidate(cache_key)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.stats()


__all__ = ["MetadataDataProvider"]
