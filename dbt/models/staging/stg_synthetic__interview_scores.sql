-- SYNTHETIC. One row per candidate, interviewer and competency: a rubric score from 1 to 5.
select
    application_id,
    interviewer_id,
    competency,
    cast(score as integer)          as score,
    cast(interviewed_on as date)    as interviewed_on
from {{ source('recruitment', 'interview_scores') }}
