select
    d::date                          as date_day,
    year(d)                          as year,
    month(d)                         as month,
    monthname(d)                     as month_name,
    date_trunc('month', d)::date     as month_start,
    dayname(d)                       as day_name,
    dayofweekiso(d) in (6, 7)        as is_weekend,
    dayofweekiso(d) in (4, 5, 6)     as is_tv_day
from (
    select dateadd(day, seq4(), '2026-01-01'::date) as d
    from table(generator(rowcount => 730))
)