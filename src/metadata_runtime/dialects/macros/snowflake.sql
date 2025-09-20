{% macro date_trunc(granularity, column) -%}
DATE_TRUNC('{{ granularity.upper() }}', {{ column }})
{%- endmacro %}

{% macro qualify(sql, condition) -%}
{{ sql }}
QUALIFY {{ condition }}
{%- endmacro %}

{% macro apply_limit(sql, limit) -%}
{{ sql }}
LIMIT {{ limit }}
{%- endmacro %}
