with orders as (
    select * from {{ref ('stg_orders')}}
    where not  is_future_dated
), 

items as (
    select 
    order_id, 
    count(*) as item_count,
    sum(quantity) as units,
    sum(line_revenue)    as items_revenue
from {{ ref('stg_order_items') }}
group by order_id
),

shipments as (
    select order_id,carrier, is_late, delivery_days 
    from {{ref ('stg_shipments')}}
),

returns as (
    select order_id, count(*) as returned_items
    from {{ref('stg_returns')}}
    group by order_id
),

reviews as (
    select order_id, stars
    from {{ ref('stg_reviews') }}
)


select 
o.order_id,
o.customer_id,
o.ordered_at , 
o.ordered_at::date as order_date, 
o.status,
o.is_paid, 
o.channel,
o.device, 
o.promo_code, 
o.city,
o.net_revenue,
o.shipping_fee, 
i.item_count,
i.units,
s.is_late,
s.delivery_days, 
s.carrier,
coalesce(r.returned_items, 0) as returned_items,
coalesce(r.returned_items,0 )> 0 as has_return,
rv.stars
from orders o
left join items i  on o.order_id = i.order_id
left join shipments s  on o.order_id = s.order_id
left join returns   r  on o.order_id = r.order_id
left join reviews   rv on o.order_id = rv.order_id