select
    department_id,
    department_name
from {{ source('bronze', 'departments') }}
