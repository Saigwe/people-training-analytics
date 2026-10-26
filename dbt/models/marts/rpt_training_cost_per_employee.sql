-- Training spend per employee by year and department. The denominator is everyone on payroll at any point in the year,
-- so people who trained nothing still count.
with years as (
    select unnest(range(2021, 2026)) as training_year
),

on_payroll as (
    select y.training_year, e.department, e.employee_id
    from years y
    join {{ ref('dim_employee') }} e
      on e.hire_date <= make_date(y.training_year, 12, 31)
     and coalesce(e.exit_date, date '9999-12-31') >= make_date(y.training_year, 1, 1)
),

spend as (
    select training_year, department, employee_id, count(*) as trainings, sum(cost_gbp) as cost_gbp, sum(hours) as hours
    from {{ ref('fct_training') }}
    group by all
)

select
    p.training_year,
    p.department,
    count(*)                                              as employees_on_payroll,
    count(s.employee_id)                                  as employees_trained,
    coalesce(sum(s.trainings), 0)                         as trainings,
    coalesce(sum(s.cost_gbp), 0)                          as training_cost_gbp,
    round(coalesce(sum(s.cost_gbp), 0) / count(*), 2)     as cost_per_employee_gbp,
    round(coalesce(sum(s.hours), 0) / count(*), 2)        as hours_per_employee
from on_payroll p
left join spend s using (training_year, department, employee_id)
group by all
