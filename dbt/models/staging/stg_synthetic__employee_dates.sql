-- SYNTHETIC: employment dates (see ingestion/generate_training.py).
select employee_id, cast(hire_date as date) as hire_date, cast(exit_date as date) as exit_date
from {{ source('bronze', 'employee_dates') }}
