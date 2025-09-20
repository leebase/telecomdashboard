{% macro date_trunc(granularity, column) -%}
CASE '{{ granularity.lower() }}'
  WHEN 'day' THEN DATE({{ column }})
  WHEN 'week' THEN DATE({{ column }}, 'weekday 0', '-6 days')
  WHEN 'month' THEN DATE({{ column }}, 'start of month')
  WHEN 'quarter' THEN DATE({{ column }}, 'start of month', ((CAST(STRFTIME('%m', {{ column }}) AS INTEGER) - 1) / 3) * -1 || ' months')
  WHEN 'year' THEN DATE({{ column }}, 'start of year')
  ELSE DATE({{ column }})
END
{%- endmacro %}

{% macro qualify(sql, condition) -%}
SELECT * FROM (
  {{ sql }}
) WHERE {{ condition }}
{%- endmacro %}

{% macro apply_limit(sql, limit) -%}
{{ sql }}
LIMIT {{ limit }}
{%- endmacro %}
