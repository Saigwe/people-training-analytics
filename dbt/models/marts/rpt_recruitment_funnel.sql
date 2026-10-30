-- The hiring funnel: how many applications reached each stage, and the conversion from the stage before, for every
-- role and source channel and for all hiring together (grouping sets). SYNTHETIC.
with reached as (
    select a.job_role, a.source_channel, e.stage, e.stage_order, count(*) as applications
    from {{ ref('stg_synthetic__application_events') }} e
    join {{ ref('stg_synthetic__applications') }} a using (application_id)
    group by grouping sets ((a.job_role, e.stage, e.stage_order), (a.source_channel, e.stage, e.stage_order),
                            (e.stage, e.stage_order))
),

labelled as (
    select
        case when job_role is not null then 'role' when source_channel is not null then 'source' else 'all' end as cut,
        coalesce(job_role, source_channel, 'All hiring')                     as segment,
        stage,
        stage_order,
        applications
    from reached
)

select
    cut,
    segment,
    stage,
    stage_order,
    applications,
    round(applications / lag(applications) over (partition by cut, segment order by stage_order), 4) as conversion_from_previous,
    round(applications / first_value(applications) over (partition by cut, segment order by stage_order), 4) as share_of_applicants
from labelled
