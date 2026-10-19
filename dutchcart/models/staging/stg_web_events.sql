with source as (
    select * from {{ source('raw', 'web_events') }}
),

renamed as (
    select
        record:event_id::string        as event_id,
        record:session_id::string      as session_id,
        record:customer_id::string     as customer_id,
        record:event_name::string      as event_name,
        record:product_id::string      as product_id,
        record:channel::string         as channel,
        record:device::string          as device,
        record:event_ts::timestamp     as event_at,
        file_name,
        loaded_at
    from source
)

select *
from renamed
qualify row_number() over (partition by event_id order by loaded_at) = 1