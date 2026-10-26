select
    "O*NET-SOC Code" as onet_soc_code,
    "Title"          as onet_title
from {{ source('bronze', 'onet_occupations') }}
