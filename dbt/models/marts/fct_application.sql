-- One row per application: how far it got, when, and how long each step took. SYNTHETIC.
with stages as (
    select
        application_id,
        max(stage_order)                                                    as furthest_stage_order,
        max(case when stage = 'screened' then stage_date end)               as screened_on,
        max(case when stage = 'assessed' then stage_date end)               as assessed_on,
        max(case when stage = 'interviewed' then stage_date end)            as interviewed_on,
        max(case when stage = 'offered' then stage_date end)                as offered_on,
        max(case when stage = 'accepted' then stage_date end)               as accepted_on,
        max(case when stage = 'started' then stage_date end)                as started_on
    from {{ ref('stg_synthetic__application_events') }}
    group by 1
)

select
    a.application_id,
    a.requisition_id,
    a.job_role,
    a.source_channel,
    a.applied_on,
    s.screened_on,
    s.assessed_on,
    s.interviewed_on,
    s.offered_on,
    s.accepted_on,
    s.started_on,
    case s.furthest_stage_order
        when 1 then 'applied' when 2 then 'screened' when 3 then 'assessed' when 4 then 'interviewed'
        when 5 then 'offered' when 6 then 'accepted' when 7 then 'started'
    end                                                                     as furthest_stage,
    s.furthest_stage_order,
    s.offered_on is not null                                                as was_offered,
    s.started_on is not null                                                as was_hired,
    datediff('day', a.applied_on, s.offered_on)                             as days_to_offer,
    datediff('day', a.applied_on, s.started_on)                             as days_to_start
from {{ ref('stg_synthetic__applications') }} a
join stages s using (application_id)
