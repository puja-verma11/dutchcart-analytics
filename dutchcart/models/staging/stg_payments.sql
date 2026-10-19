with source as (
    select * from {{ source('raw', 'payments') }}
),

unpacked_to_stg as (
    select
        record:payment_id::string        as payment_id,
        record:order_id::string          as order_id,
        record:method::string            as payment_method,
        record:amount::number(10,2)      as amount,
        record:status::string            as payment_status,
        record:payment_ts::timestamp     as paid_at,
        file_name,
        loaded_at
    from source
)

select
    *,
    payment_status = 'failed' as is_failed
from unpacked_to_stg