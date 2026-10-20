{#
  Cross-database helpers: the same model SQL runs on Snowflake and on DuckDB.
  dbt fills in the right syntax for the database we build on (target.type).
#}

{# Read one field from the RECORD json column and give it a type.
   json_field('order_id', 'string')  ->  Snowflake: record:order_id::string
                                         DuckDB:    cast(record->>'order_id' as varchar) #}
{% macro json_field(field, type) -%}
    {%- if target.type == 'duckdb' -%}
        cast(record->>'{{ field }}' as {{ duckdb_type(type) }})
    {%- else -%}
        record:{{ field }}::{{ type }}
    {%- endif -%}
{%- endmacro %}

{# Translate the Snowflake type names we use into DuckDB type names #}
{% macro duckdb_type(type) -%}
    {%- set t = type | lower -%}
    {%- if t == 'string' -%} varchar
    {%- elif t == 'int' -%} integer
    {%- elif t.startswith('number') -%} {{ t | replace('number', 'decimal') }}
    {%- else -%} {{ t }}
    {%- endif -%}
{%- endmacro %}

{# TRUE when a json field arrived as text, e.g. "€19,99" instead of 19.99 #}
{% macro json_field_is_text(field) -%}
    {%- if target.type == 'duckdb' -%}
        json_type(record, '$.{{ field }}') = 'VARCHAR'
    {%- else -%}
        typeof(record:{{ field }}) = 'VARCHAR'
    {%- endif -%}
{%- endmacro %}

{# Text -> decimal number; gives NULL instead of an error when it can't convert #}
{% macro safe_to_decimal(expression) -%}
    {%- if target.type == 'duckdb' -%}
        try_cast({{ expression }} as decimal(10, 2))
    {%- else -%}
        try_to_number({{ expression }}, 10, 2)
    {%- endif -%}
{%- endmacro %}

{# ISO day of the week: Monday = 1 ... Sunday = 7 #}
{% macro iso_day_of_week(date_expression) -%}
    {%- if target.type == 'duckdb' -%}
        isodow({{ date_expression }})
    {%- else -%}
        dayofweekiso({{ date_expression }})
    {%- endif -%}
{%- endmacro %}

{# One row per day between two dates (start included, end excluded), column name: d #}
{% macro date_rows(start_date, end_date) -%}
    {%- if target.type == 'duckdb' -%}
        select cast(range as date) as d
        from range(date '{{ start_date }}', date '{{ end_date }}', interval 1 day)
    {%- else -%}
        select d from (
            select dateadd(day, row_number() over (order by seq4()) - 1, '{{ start_date }}'::date) as d
            from table(generator(rowcount => 3000))
        )
        where d < '{{ end_date }}'::date
    {%- endif -%}
{%- endmacro %}
