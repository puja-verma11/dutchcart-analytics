with source as (
    select * from {{ source('raw', 'returns') }}
),

renamed as (
    select
        {{ json_field('return_id', 'string') }}       as return_id,
        {{ json_field('order_id', 'string') }}        as order_id,
        {{ json_field('product_id', 'string') }}      as product_id,
        {{ json_field('reason', 'string') }}          as return_reason,
        {{ json_field('return_ts', 'timestamp') }}    as returned_at,
        file_name,
        loaded_at
    from source
)

select
    *,
    return_reason = 'late_delivery' as is_due_to_late_delivery
from renamed