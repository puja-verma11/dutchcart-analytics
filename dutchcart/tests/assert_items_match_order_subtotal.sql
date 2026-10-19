-- fails if the items of an order don't add up to the order's subtotal
with items as (
    select order_id, sum(line_revenue) as items_total
    from {{ ref('stg_order_items') }}
    group by order_id
)
select o.order_id, o.subtotal, i.items_total
from {{ ref('stg_orders') }} o
join items i on o.order_id = i.order_id
where abs(o.subtotal - i.items_total) > 0.01