with source as (

    select * from {{ source('raw', 'orders') }}

),

unpacked_to_stg as (

    select
        record:order_id::string            as order_id,
        record:customer_id::string         as customer_id,
        record:session_id::string          as session_id,
        record:order_ts::timestamp         as ordered_at,
        record:status::string              as status,
        record:channel::string             as channel,
        record:device::string              as device,
        record:promo_code::string          as promo_code,
        record:subtotal::number(10,2)      as subtotal,
        record:discount::number(10,2)      as discount,
        record:shipping_fee::number(10,2)  as shipping_fee,
        record:city::string                as city,
        record:postcode::string            as postcode,
        file_name,
        loaded_at
    from source

),


cleaned as (

    select
        *,
        subtotal - discount                 as net_revenue,
        status = 'paid'                     as is_paid,
        ordered_at > current_timestamp()    as is_future_dated,
        postcode is null                    as is_missing_postcode
    from unpacked_to_stg

)

select * from cleaned
