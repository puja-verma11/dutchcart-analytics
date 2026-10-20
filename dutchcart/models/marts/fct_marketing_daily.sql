with spend as (
    select spend_date as activity_date, channel, spend_eur, clicks, impressions
    from dutchcart.staging.stg_marketing_spend
),

visits as (
    select event_at::date as activity_date, channel,
           count(distinct session_id) as sessions
    from dutchcart.staging.stg_web_events
    group by 1, 2
),

sales as (
    select order_date as activity_date, channel,
           count(*) as orders, sum(net_revenue) as revenue
    from dutchcart.marts.fct_orders
    where is_paid
    group by 1, 2
),

joined as (
    select
        coalesce(s.activity_date, v.activity_date, o.activity_date) as activity_date,
        coalesce(s.channel, v.channel, o.channel)                   as channel,
        coalesce(s.spend_eur, 0)  as spend_eur,
        s.clicks,
        s.impressions,
        coalesce(v.sessions, 0)   as sessions,
        coalesce(o.orders, 0)     as orders,
        coalesce(o.revenue, 0)    as revenue
    from spend s
    full outer join visits v
        on s.activity_date = v.activity_date and s.channel = v.channel
    full outer join sales o
        on coalesce(s.activity_date, v.activity_date) = o.activity_date
       and coalesce(s.channel, v.channel) = o.channel
)

select
    activity_date || '-' || channel              as marketing_day_id,
    *,
    channel in ('tv', 'radio')                   as is_offline,
    round(revenue / nullif(spend_eur, 0), 2)     as roas,
    round(spend_eur / nullif(orders, 0), 2)      as cost_per_order
from joined
order by activity_date, channel