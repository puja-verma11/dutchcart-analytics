with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select order_id, order_date, channel, customer_id
    from {{ ref('fct_orders') }}
    where is_paid
),

returns as (
    select order_id, product_id, count(*) as returned_qty
    from {{ ref('stg_returns') }}
    group by 1, 2
)

select
    i.order_id || '-' || row_number() over (partition by i.order_id order by i.product_id)  as order_item_id,
    i.order_id,
    i.product_id,
    o.customer_id,
    o.order_date,
    o.channel,
    i.quantity,
    i.unit_price,
    i.line_revenue,
    coalesce(r.returned_qty, 0) > 0    as is_returned
from items i
join orders o
    on i.order_id = o.order_id
left join returns r
    on i.order_id = r.order_id and i.product_id = r.product_id