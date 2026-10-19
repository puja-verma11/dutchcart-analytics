with source as (
    select * from {{ source('raw', 'inventory_snapshots') }}
),

renamed as (
    select
        record:snapshot_date::date     as snapshot_date,
        record:product_id::string      as product_id,
        record:stock::int              as stock,
        file_name,
        loaded_at
    from source
)

select
    snapshot_date || '-' || product_id   as snapshot_id,
    *,
    stock = 0                            as is_out_of_stock
from renamed
