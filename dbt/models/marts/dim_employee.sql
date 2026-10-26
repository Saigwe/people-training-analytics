-- One row per employee: real IBM attributes, synthetic employment dates, and the O*NET occupation for the role.
select
    e.*,
    d.hire_date,
    d.exit_date,
    m.onet_soc_code,
    o.onet_title,
    case
        when e.training_times_last_year = 0 then '0'
        when e.training_times_last_year <= 2 then '1-2'
        when e.training_times_last_year <= 4 then '3-4'
        else '5-6'
    end as training_band
from {{ ref('stg_ibm__employees') }} e
join {{ ref('stg_synthetic__employee_dates') }} d using (employee_id)
join {{ ref('job_role_onet') }} m using (job_role)
join {{ ref('stg_onet__occupations') }} o using (onet_soc_code)
