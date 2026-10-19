with source as(
    select * from  {{source('raw' , 'customers')}}
),

renamed as (
    select 
    record:customer_id::string as customer_id,
    record:email::string as email,
    record:city::string            as city,
        record:postcode::string        as postcode,
        record:signup_ts::timestamp    as signed_up_at,
        file_name,
        loaded_at
    from source

)
select
    *,
    email is null as is_missing_email
from renamed