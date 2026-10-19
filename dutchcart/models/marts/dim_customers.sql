-- One row per customer: who they are + what they did (orders, spend, returns, reviews).
-- Only PAID orders count as sales.

with customers as (
    select * from {{ ref('stg_customers') }}
),

orders as (
    select * from {{ ref('fct_orders') }}
    where is_paid
),

customer_orders as (
    select
        customer_id,
        count(*)                        as total_orders,
        sum(net_revenue)                as lifetime_revenue,
        avg(net_revenue)                as avg_order_value,
        min(order_date)                 as first_order_date,
        max(order_date)                 as last_order_date,
        sum(returned_items)             as total_returned_items,
        avg(stars)                      as avg_stars
    from orders
    group by customer_id
)

select
    c.customer_id,
    c.city,
    c.signed_up_at,
    c.is_missing_email,
    coalesce(o.total_orders, 0)                  as total_orders,
    coalesce(o.lifetime_revenue, 0)              as lifetime_revenue,
    round(o.avg_order_value, 2)                  as avg_order_value,
    o.first_order_date,
    o.last_order_date,
    coalesce(o.total_returned_items, 0)          as total_returned_items,
    round(o.avg_stars, 1)                        as avg_stars,
    coalesce(o.total_orders, 0) > 1              as is_repeat_customer,
    case
        when o.lifetime_revenue >= 500 then 'high'
        when o.lifetime_revenue >= 150 then 'medium'
        else 'low'
    end                                          as value_segment
from customers c
left join customer_orders o on c.customer_id = o.customer_id
