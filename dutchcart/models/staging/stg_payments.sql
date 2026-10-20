with source as (
    select * from {{ source('raw', 'payments') }}
),

unpacked_to_stg as (
    select
        {{ json_field('payment_id', 'string') }}        as payment_id,
        {{ json_field('order_id', 'string') }}          as order_id,
        {{ json_field('method', 'string') }}            as payment_method,
        {{ json_field('amount', 'number(10,2)') }}      as amount,
        {{ json_field('status', 'string') }}            as payment_status,
        {{ json_field('payment_ts', 'timestamp') }}     as paid_at,
        file_name,
        loaded_at
    from source
)

select
    *,
    payment_status = 'failed' as is_failed
from unpacked_to_stg