-- A funnel can only narrow: no stage may have more applications than the stage before it, in any segment, and
-- every application's stage dates must run forward in time.
select 'stage count rose' as problem, cut || ' / ' || segment || ' / ' || stage as detail
from {{ ref('rpt_recruitment_funnel') }}
where conversion_from_previous > 1
union all
select 'stage dates out of order', application_id
from {{ ref('fct_application') }}
where screened_on < applied_on or assessed_on < screened_on or interviewed_on < assessed_on
   or offered_on < interviewed_on or accepted_on < offered_on or started_on < accepted_on
