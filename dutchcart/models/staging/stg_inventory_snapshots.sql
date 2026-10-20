with source as (
    select * from {{ source('raw', 'inventory_snapshots') }}
),

renamed as (
    select
        {{ json_field('snapshot_date', 'date') }}     as snapshot_date,
        {{ json_field('product_id', 'string') }}      as product_id,
        {{ json_field('stock', 'int') }}              as stock,
        file_name,
        loaded_at
    from source
)

select
    cast(snapshot_date as varchar) || '-' || product_id   as snapshot_id,
    *,
    stock = 0                            as is_out_of_stock
from renamed
