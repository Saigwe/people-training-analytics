-- SYNTHETIC: one row per course completion.
select training_id, employee_id, course_id, cast(completed_on as date) as completed_on
from {{ source('bronze', 'trainings') }}
