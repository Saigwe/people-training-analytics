-- The synthetic history keeps the real field: each employee's completions in their last year (2025) equal IBM's
-- TrainingTimesLastYear.
select e.employee_id, e.training_times_last_year, count(t.training_id) as completions
from {{ ref('dim_employee') }} e
left join {{ ref('fct_training') }} t
  on t.employee_id = e.employee_id and t.training_year = year(coalesce(e.exit_date, date '2025-12-31'))
group by all
having count(t.training_id) <> e.training_times_last_year
