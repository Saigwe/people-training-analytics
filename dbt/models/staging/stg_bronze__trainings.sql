select
    training_id,
    employee_id,
    cast(training_date as date)           as training_date,
    course,
    cost_usd,
    hours
from {{ source('bronze', 'trainings') }}
