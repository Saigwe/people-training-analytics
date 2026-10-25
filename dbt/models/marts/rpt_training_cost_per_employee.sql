-- Training spend per employee by year and department (employees on payroll at any point in the year).
with years as (
    select distinct extract(year from training_date) as training_year from {{ ref('stg_bronze__trainings') }}
),

headcount as (
    select y.training_year, e.department_id, count(*) as employees
    from years y
    join {{ ref('stg_bronze__employees') }} e
        on extract(year from e.hire_date) <= y.training_year
        and (e.leave_date is null or extract(year from e.leave_date) >= y.training_year)
    group by 1, 2
),

spend as (
    select extract(year from t.training_date) as training_year, e.department_id,
           sum(t.cost_usd) as cost_usd, sum(t.hours) as hours
    from {{ ref('stg_bronze__trainings') }} t
    join {{ ref('stg_bronze__employees') }} e on e.employee_id = t.employee_id
    group by 1, 2
)

select
    h.training_year,
    h.department_id,
    h.employees,
    coalesce(s.cost_usd, 0)                     as cost_usd,
    coalesce(s.hours, 0)                        as hours,
    coalesce(s.cost_usd, 0) / h.employees       as cost_per_employee_usd
from headcount h
left join spend s on s.training_year = h.training_year and s.department_id = h.department_id
