with source as (
    select * from {{ source('raw', 'returns') }}
),

renamed as (
    select
        record:return_id::string       as return_id,
        record:order_id::string        as order_id,
        record:product_id::string      as product_id,
        record:reason::string          as return_reason,
        record:return_ts::timestamp    as returned_at,
        file_name,
        loaded_at
    from source
)

select
    *,
    return_reason = 'late_delivery' as is_due_to_late_delivery
from renamed