-- One row per day (2026-2027): a calendar for grouping by month, weekday, TV days.
with days as (
    {{ date_rows('2026-01-01', '2028-01-01') }}
)

select
    d                                              as date_day,
    year(d)                                        as year,
    month(d)                                       as month,
    monthname(d)                                   as month_name,
    cast(date_trunc('month', d) as date)           as month_start,
    dayname(d)                                     as day_name,
    {{ iso_day_of_week('d') }} in (6, 7)           as is_weekend,
    {{ iso_day_of_week('d') }} in (4, 5, 6)        as is_tv_day
from days
