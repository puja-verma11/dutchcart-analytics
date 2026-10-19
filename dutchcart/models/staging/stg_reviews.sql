with source as (
    select * from {{ source('raw', 'reviews') }}
),

renamed as (
    select
        record:review_id::string       as review_id,
        record:order_id::string        as order_id,
        record:stars::int              as stars,
        record:review_ts::timestamp    as reviewed_at,
        file_name,
        loaded_at
    from source
)

select
    *,
    stars <= 2 as is_negative_review
from renamed