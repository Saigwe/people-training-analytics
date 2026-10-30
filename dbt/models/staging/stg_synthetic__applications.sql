-- SYNTHETIC. One row per application, with the requisition's role and openings.
select
    a.application_id,
    a.requisition_id,
    r.job_role,
    r.openings,
    a.source_channel,
    cast(a.applied_on as date) as applied_on
from {{ source('recruitment', 'applications') }} a
join {{ source('recruitment', 'requisitions') }} r using (requisition_id)
