-- SYNTHETIC. One row per application per stage reached, with the stage's order in the funnel.
select
    application_id,
    stage,
    cast(stage_date as date) as stage_date,
    case stage
        when 'applied' then 1 when 'screened' then 2 when 'assessed' then 3 when 'interviewed' then 4
        when 'offered' then 5 when 'accepted' then 6 when 'started' then 7
    end as stage_order
from {{ source('recruitment', 'application_events') }}
