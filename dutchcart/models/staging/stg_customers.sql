with source as(
    select * from  {{source('raw' , 'customers')}}
),

renamed as (
    select 
    {{ json_field('customer_id', 'string') }} as customer_id,
    {{ json_field('email', 'string') }} as email,
    {{ json_field('city', 'string') }}            as city,
        {{ json_field('postcode', 'string') }}        as postcode,
        {{ json_field('signup_ts', 'timestamp') }}    as signed_up_at,
        file_name,
        loaded_at
    from source

)
select
    *,
    email is null as is_missing_email
from renamed