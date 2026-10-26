-- SYNTHETIC: course catalogue, one course per O*NET skill.
select course_id, course_name, skill_id, skill, format as course_format, cost_gbp, hours
from {{ source('bronze', 'course_catalog') }}
