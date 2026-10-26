-- Each role's gap rows cover exactly the role's active headcount, for all 8 skills.
with active as (
    select job_role, count(*) as headcount from {{ ref('dim_employee') }} where exit_date is null group by all
)

select g.job_role, g.skill_id
from {{ ref('rpt_competency_gap_matrix') }} g
join active a using (job_role)
where g.employees <> a.headcount
union all
select job_role, null from {{ ref('rpt_competency_gap_matrix') }} group by job_role having count(*) <> 8
