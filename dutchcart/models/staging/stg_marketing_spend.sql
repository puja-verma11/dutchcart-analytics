with source as (
    select * from {{ source('raw', 'marketing_spend') }}
),

renamed as (
    select
        {{ json_field('spend_date', 'date') }}           as spend_date,
        {{ json_field('channel', 'string') }}            as channel,
        {{ json_field('spend_eur', 'number(10,2)') }}    as spend_eur,
        {{ json_field('clicks', 'int') }}                as clicks,
        {{ json_field('impressions', 'int') }}           as impressions,
        file_name,
        loaded_at
    from source
)

select
    cast(spend_date as varchar) || '-' || channel   as spend_id,
    *
from renamed
