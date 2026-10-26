-- Required vs achieved competency, by job role and skill, for employees still on payroll at the snapshot.
-- Required levels are REAL (O*NET). Achieved levels are a SYNTHETIC, transparent model, since no HR system records them:
--   base = required level x clip(0.55 + 0.08 x job level + 0.01 x total working years + 0.03 x (performance rating - 3), 0.4, 1.1)
--   achieved = min(7, base + 0.3 per completed course on that skill)
with active as (
    select * from {{ ref('dim_employee') }} where exit_date is null
),

courses_done as (
    select employee_id, skill_id, count(*) as courses
    from {{ ref('fct_training') }}
    group by all
),

assessed as (
    select
        a.job_role,
        r.skill_id,
        r.skill,
        r.skill_rank,
        r.importance,
        r.required_level,
        a.employee_id,
        coalesce(c.courses, 0) as courses_on_skill,
        least(7.0,
              r.required_level * greatest(0.4, least(1.1, 0.55 + 0.08 * a.job_level + 0.01 * a.total_working_years
                                                       + 0.03 * (a.performance_rating - 3)))
              + 0.3 * coalesce(c.courses, 0)) as achieved_level
    from active a
    join {{ ref('rpt_competency_requirements') }} r using (job_role)
    left join courses_done c using (employee_id, skill_id)
)

select
    job_role,
    skill_id,
    skill,
    skill_rank,
    importance,
    required_level,
    count(*)                                                                      as employees,
    round(avg(achieved_level), 2)                                                 as avg_achieved_level,
    round(avg(greatest(required_level - achieved_level, 0)), 2)                   as avg_gap,
    round(avg(case when achieved_level >= required_level then 1.0 else 0 end), 3) as share_meeting_requirement,
    round(avg(case when courses_on_skill > 0 then 1.0 else 0 end), 3)             as share_trained_on_skill
from assessed
group by all
