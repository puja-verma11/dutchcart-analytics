with source as (
    select * from {{ source('raw', 'web_events') }}
),

renamed as (
    select
        {{ json_field('event_id', 'string') }}        as event_id,
        {{ json_field('session_id', 'string') }}      as session_id,
        {{ json_field('customer_id', 'string') }}     as customer_id,
        {{ json_field('event_name', 'string') }}      as event_name,
        {{ json_field('product_id', 'string') }}      as product_id,
        {{ json_field('channel', 'string') }}         as channel,
        {{ json_field('device', 'string') }}          as device,
        {{ json_field('event_ts', 'timestamp') }}     as event_at,
        file_name,
        loaded_at
    from source
)

select *
from renamed
qualify row_number() over (partition by event_id order by loaded_at) = 1