-- REAL: the skills each job role needs, from O*NET: the role's top 8 skills by importance, with the required level.
select
    m.job_role,
    m.onet_soc_code,
    s.skill_id,
    s.skill,
    s.importance,
    s.required_level,
    row_number() over (partition by m.job_role order by s.importance desc, s.required_level desc, s.skill_id) as skill_rank
from {{ ref('job_role_onet') }} m
join {{ ref('stg_onet__skills') }} s using (onet_soc_code)
where not s.level_not_relevant
qualify skill_rank <= 8
