-- Every completion falls between the employee's hire date and exit date (or the 31 Dec 2025 snapshot).
select t.training_id
from {{ ref('fct_training') }} t
join {{ ref('dim_employee') }} e using (employee_id)
where t.completed_on < e.hire_date
   or t.completed_on > coalesce(e.exit_date, date '2025-12-31')
