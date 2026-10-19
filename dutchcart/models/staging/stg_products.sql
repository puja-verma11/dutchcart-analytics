with source as (
    select * from {{ source('raw', 'products') }}
),

renamed as (

    select
        record:product_id::string        as product_id,
        record:product_name::string      as product_name,
        record:category::string          as category,
        record:price::number(10,2)       as price,
        record:cost::number(10,2)        as cost,
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