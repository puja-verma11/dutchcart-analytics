with source as (
    select * from {{ source('raw', 'order_items') }}
),

renamed as (

    select
        record:order_id::string                           as order_id,
        record:product_id::string                         as product_id,
        record:quantity::int                              as quantity,
        -- text price -> remove €, swap Dutch comma for a dot, make it a number
        try_to_number(
            replace(replace(record:unit_price::string, '€', ''), ',', '.'),
            10, 2
        )                                                 as unit_price,
        typeof(record:unit_price) = 'VARCHAR'             as was_price_text,
        file_name,
        loaded_at
    from source

)

select
    *,
    quantity * unit_price as line_revenue
from renamed