with source as (
    select * from {{ source('raw', 'marketing_spend') }}
),

renamed as (
    select
        record:spend_date::date           as spend_date,
        record:channel::string            as channel,
        record:spend_eur::number(10,2)    as spend_eur,
        record:clicks::int                as clicks,
        record:impressions::int           as impressions,
        file_name,
        loaded_at
    from source
)

select
    spend_date || '-' || channel   as spend_id,
    *
from renamed
