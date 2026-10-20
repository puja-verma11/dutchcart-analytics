with source as (

    select * from {{ source('raw', 'orders') }}

),

unpacked_to_stg as (

    select
        {{ json_field('order_id', 'string') }}            as order_id,
        {{ json_field('customer_id', 'string') }}         as customer_id,
        {{ json_field('session_id', 'string') }}          as session_id,
        {{ json_field('order_ts', 'timestamp') }}         as ordered_at,
        {{ json_field('status', 'string') }}              as status,
        {{ json_field('channel', 'string') }}             as channel,
        {{ json_field('device', 'string') }}              as device,
        {{ json_field('promo_code', 'string') }}          as promo_code,
        {{ json_field('subtotal', 'number(10,2)') }}      as subtotal,
        {{ json_field('discount', 'number(10,2)') }}      as discount,
        {{ json_field('shipping_fee', 'number(10,2)') }}  as shipping_fee,
        {{ json_field('city', 'string') }}                as city,
        {{ json_field('postcode', 'string') }}            as postcode,
        file_name,
        loaded_at
    from source

),


cleaned as (

    select
        *,
        subtotal - discount                 as net_revenue,
        status = 'paid'                     as is_paid,
        ordered_at > current_timestamp    as is_future_dated,
        postcode is null                    as is_missing_postcode
    from unpacked_to_stg

)

select * from cleaned
