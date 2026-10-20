with source as (
    select * from {{ source('raw', 'shipments') }}
),

renamed as (
    select
        {{ json_field('shipment_id', 'string') }}       as shipment_id,
        {{ json_field('order_id', 'string') }}          as order_id,
        {{ json_field('carrier', 'string') }}           as carrier,
        {{ json_field('shipped_ts', 'timestamp') }}     as shipped_at,
        {{ json_field('promised_date', 'date') }}       as promised_date,
        {{ json_field('delivered_date', 'date') }}      as delivered_date,
        file_name,
        loaded_at
    from source
)

select
    *,
    delivered_date is null                             as is_missing_delivery_date,
    delivered_date > promised_date                     as is_late,
    datediff('day', shipped_at::date, delivered_date)  as delivery_days
from renamed