select
    product_id,
    product_name,
    category,
    price,
    cost,
    unit_margin,
    round(unit_margin / nullif(price, 0), 2)   as margin_pct
from {{ ref('stg_products') }}