with source as (
    select * from {{ source('raw', 'order_items') }}
),

renamed as (

    select
        {{ json_field('order_id', 'string') }}      as order_id,
        {{ json_field('product_id', 'string') }}    as product_id,
        {{ json_field('quantity', 'int') }}         as quantity,
        -- text price -> remove €, swap Dutch comma for a dot, make it a number
        {{ safe_to_decimal(
            "replace(replace(" ~ json_field('unit_price', 'string') ~ ", '€', ''), ',', '.')"
        ) }}                                        as unit_price,
        {{ json_field_is_text('unit_price') }}      as was_price_text,
        file_name,
        loaded_at
    from source

)

select
    *,
    quantity * unit_price as line_revenue
from renamed
