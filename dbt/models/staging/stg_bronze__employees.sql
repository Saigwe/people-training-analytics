select
    employee_id,
    department_id,
    job_family,
    cast(hire_date as date)               as hire_date,
    cast(leave_date as date)              as leave_date
from {{ source('bronze', 'employees') }}
