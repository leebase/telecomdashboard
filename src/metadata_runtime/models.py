"""Pydantic models for metadata-driven dashboard configuration.

These models intentionally mirror the schema documented in
``docs/refactor/SCHEMA.md`` and power the metadata validation CLI.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator


class NumberFormat(BaseModel):
    decimal_places: int = Field(0, ge=0)
    compact_units: bool = False


class GlobalsConfig(BaseModel):
    timezone: str
    default_date_range: str = Field(..., alias="default_date_range")
    currency: Optional[str]
    theme: Optional[str]
    number_format: Optional[NumberFormat]
    ai_insights_enabled: bool = True
    print_mode_enabled: bool = False

    class Config:
        allow_population_by_field_name = True


class DialectMacros(BaseModel):
    snowflake: Optional[str]
    sqlite: Optional[str]


class DialectsConfig(BaseModel):
    default: str
    supported: List[str] = Field(default_factory=list)
    macros: Optional[DialectMacros]

    @validator("supported", pre=True, always=True, allow_reuse=True)
    def ensure_supported(cls, value):
        return list(value or [])

    @root_validator
    def validate_default(cls, values):
        default = values.get("default")
        supported = values.get("supported") or []
        if default and supported and default not in supported:
            raise ValueError(f"Default dialect '{default}' must be in supported list")
        return values


class DataSourceConfig(BaseModel):
    dialect: str
    dsn_env: Optional[str]
    path: Optional[str]
    role: Optional[str]
    warehouse: Optional[str]
    database: Optional[str]
    schema_name: Optional[str] = Field(default=None, alias="schema")
    read_only: bool = False

    class Config:
        allow_population_by_field_name = True

    @root_validator
    def validate_connection(cls, values):
        dialect = values.get("dialect")
        if dialect == "snowflake" and not values.get("dsn_env"):
            raise ValueError("Snowflake data sources require 'dsn_env'")
        if dialect == "sqlite" and not values.get("path"):
            raise ValueError("SQLite data sources require 'path'")
        return values

    @property
    def schema(self) -> Optional[str]:  # pragma: no cover - simple alias
        return self.schema_name


class FilterBindings(BaseModel):
    start_param: Optional[str]
    end_param: Optional[str]


class FilterConfig(BaseModel):
    id: str
    type: str
    label: Optional[str]
    default: Optional[Union[str, int, float, bool]]
    options: Optional[List[Union[str, int, float]]]
    data_source: Optional[str]
    sql: Optional[str]
    allow_blank: bool = False
    multi: Optional[bool]
    depends_on: Optional[str]
    bindings: Optional[FilterBindings]

    @root_validator
    def validate_source(cls, values):
        filter_type = values.get("type")
        sql = values.get("sql")
        data_source = values.get("data_source")
        if sql and not data_source:
            raise ValueError("Filters referencing SQL must specify a data_source")
        if filter_type == "date_range":
            bindings = values.get("bindings")
            if not bindings or not bindings.start_param or not bindings.end_param:
                raise ValueError("Date range filters require start/end bindings")
        return values


class LayoutSlot(BaseModel):
    kpi_card: Optional[str]
    chart: Optional[str]
    widget: Optional[str]

    @root_validator
    def exactly_one_reference(cls, values):
        populated = [key for key, value in values.items() if value]
        if len(populated) != 1:
            raise ValueError("Layout slot must reference exactly one item (kpi_card, chart, or widget)")
        return values


class LayoutSection(BaseModel):
    id: str
    title: Optional[str]
    rows: List[List[LayoutSlot]] = Field(default_factory=list)

    @validator("rows", each_item=True)
    def validate_row_width(cls, row):
        if not row:
            raise ValueError("Layout rows must contain at least one slot")
        return row


class LayoutConfig(BaseModel):
    grid_columns: int = Field(12, ge=1)
    sections: List[LayoutSection] = Field(default_factory=list)


class SubjectAreaConfig(BaseModel):
    id: str
    title: str
    icon: Optional[str]
    order: Optional[int] = 0
    description: Optional[str]
    default_filters: List[str] = Field(default_factory=list)
    layout: LayoutConfig


class ThresholdConfig(BaseModel):
    good: Optional[str]
    warn: Optional[str]
    bad: Optional[str]


class PrimaryWidgetConfig(BaseModel):
    type: str
    dataset: str
    value_expr: Optional[str]
    delta_expr: Optional[str]
    unit: Optional[str]
    decimals: Optional[int]
    formatting: Optional[Dict[str, Union[str, int, float, bool]]]


class SecondaryWidgetConfig(BaseModel):
    chart_id: Optional[str]
    type: str
    dataset: str
    encoding: Optional[Dict[str, Union[str, int, float, List[Union[str, int, float]], Dict[str, Union[str, int, float]]]]]
    columns: Optional[List[str]]
    lower: Optional[str]
    upper: Optional[str]


class KPIWidgetsConfig(BaseModel):
    primary: PrimaryWidgetConfig
    secondary: List[SecondaryWidgetConfig] = Field(default_factory=list)


class KpiMetricConfig(BaseModel):
    id: str
    data_source: str
    sql: str
    fallback_source: Optional[str]
    dialect: Optional[str]
    dimensions: List[str] = Field(default_factory=list)
    cache_ttl_seconds: Optional[int] = Field(default=None, ge=0)
    thresholds: Optional[ThresholdConfig]


class KpiConfig(BaseModel):
    id: str
    title: str
    subject_area: str
    description: Optional[str]
    owner: Optional[str]
    tags: List[str] = Field(default_factory=list)
    metrics: List[KpiMetricConfig]
    widgets: KPIWidgetsConfig

    @validator("metrics")
    def require_metrics(cls, metrics):
        if not metrics:
            raise ValueError("KPI must define at least one metric")
        return metrics


class AuxiliaryMetricConfig(BaseModel):
    id: str
    data_source: str
    sql: str
    cache_ttl_seconds: Optional[int] = Field(default=None, ge=0)


class WidgetRegistryOverride(BaseModel):
    type: str
    dataset: str
    encoding: Optional[Dict[str, Union[str, int, float, Dict[str, Union[str, int, float]]]]]
    columns: Optional[List[str]]


class WidgetsOverridesConfig(BaseModel):
    __root__: Dict[str, WidgetRegistryOverride]

    def __iter__(self):
        return iter(self.__root__.items())


class RoleConfig(BaseModel):
    inherits: List[str] = Field(default_factory=list)
    can_view_subject_areas: List[str] = Field(default_factory=list)
    can_view_kpis: List[str] = Field(default_factory=list)
    can_edit_widgets: List[str] = Field(default_factory=list)


class RowLevelFilterConfig(BaseModel):
    __root__: Dict[str, str]


class SecurityConfig(BaseModel):
    roles: Dict[str, RoleConfig] = Field(default_factory=dict)
    row_filters: Dict[str, Dict[str, str]] = Field(default_factory=dict)


class RefreshOverrideConfig(BaseModel):
    __root__: Dict[str, int]

    @validator("__root__")
    def ensure_positive(cls, overrides):
        for key, value in overrides.items():
            if value < 0:
                raise ValueError(f"Refresh TTL for '{key}' must be >= 0")
        return overrides


class RefreshConfig(BaseModel):
    default_ttl_seconds: int = Field(300, ge=0)
    overrides: Optional[RefreshOverrideConfig]
    schedule: Optional[Dict[str, str]]


class MetadataSources(BaseModel):
    changelog: Optional[str]
    generated_on: Optional[str]
    generated_by: Optional[str]

    @validator("changelog", "generated_on", "generated_by", pre=True)
    def normalise_paths(cls, value):
        if isinstance(value, (str, Path)):
            return str(value)
        return value


class FiltersConfig(BaseModel):
    global_: List[FilterConfig] = Field(default_factory=list, alias="global")
    subject_area: Dict[str, List[FilterConfig]] = Field(default_factory=dict)

    class Config:
        allow_population_by_field_name = True


class MetadataConfig(BaseModel):
    schema_version: str
    app_version: str
    pack_id: str
    label: str
    globals: GlobalsConfig
    dialects: DialectsConfig
    data_sources: Dict[str, DataSourceConfig]
    filters: FiltersConfig
    subject_areas: List[SubjectAreaConfig]
    kpis: List[KpiConfig]
    auxiliary_metrics: List[AuxiliaryMetricConfig] = Field(default_factory=list)
    widgets: Optional[WidgetsOverridesConfig]
    security: Optional[SecurityConfig]
    refresh: Optional[RefreshConfig]
    metadata_sources: Optional[MetadataSources]

    @validator("subject_areas")
    def ensure_unique_subject_areas(cls, subject_areas):
        ids = [sa.id for sa in subject_areas]
        if len(ids) != len(set(ids)):
            raise ValueError("Subject area IDs must be unique")
        return subject_areas

    @validator("kpis")
    def ensure_unique_kpis(cls, kpis):
        ids = [kpi.id for kpi in kpis]
        if len(ids) != len(set(ids)):
            raise ValueError("KPI IDs must be unique")
        return kpis

    @root_validator
    def cross_reference(cls, values):
        data_sources = values.get("data_sources", {})
        kpis = values.get("kpis", [])
        subject_areas = {sa.id for sa in values.get("subject_areas", [])}
        auxiliary_metrics = values.get("auxiliary_metrics", [])

        valid_data_sources = set(data_sources.keys())

        for kpi in kpis:
            if kpi.subject_area not in subject_areas:
                raise ValueError(f"KPI '{kpi.id}' references unknown subject area '{kpi.subject_area}'")
            for metric in kpi.metrics:
                if metric.data_source not in valid_data_sources:
                    raise ValueError(
                        f"Metric '{metric.id}' references unknown data source '{metric.data_source}'"
                    )
                if metric.fallback_source and metric.fallback_source not in valid_data_sources:
                    raise ValueError(
                        f"Metric '{metric.id}' fallback_source '{metric.fallback_source}' not declared"
                    )
            if kpi.widgets.primary.dataset not in {
                *(metric.id for metric in kpi.metrics),
                *(metric.id for metric in auxiliary_metrics),
            }:
                raise ValueError(
                    f"KPI '{kpi.id}' primary widget dataset '{kpi.widgets.primary.dataset}' not defined"
                )
            for secondary in kpi.widgets.secondary:
                dataset_id = secondary.dataset
                defined_metric_ids = {
                    *(metric.id for metric in kpi.metrics),
                    *(metric.id for metric in auxiliary_metrics),
                }
                if dataset_id not in defined_metric_ids:
                    raise ValueError(
                        f"KPI '{kpi.id}' secondary widget dataset '{dataset_id}' not defined"
                    )

        for metric in auxiliary_metrics:
            if metric.data_source not in valid_data_sources:
                raise ValueError(
                    f"Auxiliary metric '{metric.id}' references unknown data source '{metric.data_source}'"
                )
        return values


__all__ = ["MetadataConfig"]
