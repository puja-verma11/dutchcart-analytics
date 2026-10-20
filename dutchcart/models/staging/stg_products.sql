with source as (
    select * from {{ source('raw', 'products') }}
),

renamed as (

    select
        {{ json_field('product_id', 'string') }}        as product_id,
        {{ json_field('product_name', 'string') }}      as product_name,
        {{ json_field('category', 'string') }}          as category,
        {{ json_field('price', 'number(10,2)') }}       as price,
        {{ json_field('cost', 'number(10,2)') }}        as cost,
        file_name,
        loaded_at
    from source

)

select
    *,
    price - cost as unit_margin
from renamed


-- {
--   "category": "Fashion",
--   "cost": 36.96,
--   "price": 82.14,
--   "product_id": "FAS-001",
--   "product_name": "Fashion item 1"
-- }