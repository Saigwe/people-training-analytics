-- No one can be trained before they were hired.
select t.training_id
from {{ ref('stg_bronze__trainings') }} t
join {{ ref('stg_bronze__employees') }} e on e.employee_id = t.employee_id
where t.training_date < e.hire_date
