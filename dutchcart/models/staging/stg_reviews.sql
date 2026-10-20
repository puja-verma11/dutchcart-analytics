with source as (
    select * from {{ source('raw', 'reviews') }}
),

renamed as (
    select
        {{ json_field('review_id', 'string') }}       as review_id,
        {{ json_field('order_id', 'string') }}        as order_id,
        {{ json_field('stars', 'int') }}              as stars,
        {{ json_field('review_ts', 'timestamp') }}    as reviewed_at,
        file_name,
        loaded_at
    from source
)

select
    *,
    stars <= 2 as is_negative_review
from renamed