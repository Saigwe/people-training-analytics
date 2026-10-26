-- REAL: attrition by the number of trainings in the employee's last year (IBM's TrainingTimesLastYear), overall and by
-- department. This is the raw cohort view; analysis/attrition_model.py adds controls.
with cohorts as (
    select 'All' as department, training_band, employee_id, left_company from {{ ref('dim_employee') }}
    union all
    select department, training_band, employee_id, left_company from {{ ref('dim_employee') }}
)

select
    department,
    training_band,
    count(*)                                                  as employees,
    count(*) filter (where left_company)                      as leavers,
    round(avg(case when left_company then 1.0 else 0 end), 3) as attrition_rate
from cohorts
group by all
