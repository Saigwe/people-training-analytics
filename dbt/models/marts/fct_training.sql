-- One row per course completion (SYNTHETIC), with cost, hours and the employee's department.
select
    t.training_id,
    t.employee_id,
    t.course_id,
    t.completed_on,
    year(t.completed_on) as training_year,
    e.department,
    e.job_role,
    c.skill_id,
    c.course_format,
    c.cost_gbp,
    c.hours
from {{ ref('stg_synthetic__trainings') }} t
join {{ ref('stg_synthetic__courses') }} c using (course_id)
join {{ ref('dim_employee') }} e using (employee_id)
