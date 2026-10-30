-- One row per interviewed candidate: the raw panel average (what offers were made on) and the calibrated average
-- (each interviewer's mean offset removed), the candidate's rank in their requisition on each, whether an offer
-- was made, whether the calibrated score would have made the offer list, and first-year outcomes for starters.
-- SYNTHETIC.
with averages as (
    select
        s.application_id,
        avg(s.score)                                    as raw_average,
        avg(s.score - c.mean_offset)                    as calibrated_average,
        max(case when c.calibration <> 'calibrated' then 1 else 0 end) = 1 as had_miscalibrated_interviewer
    from {{ ref('stg_synthetic__interview_scores') }} s
    join {{ ref('rpt_interviewer_calibration') }} c using (interviewer_id)
    group by 1
),

offers_per_req as (
    select requisition_id, count(*) filter (where was_offered) as offers_made
    from {{ ref('fct_application') }}
    group by 1
),

ranked as (
    select
        f.application_id,
        f.requisition_id,
        f.job_role,
        f.source_channel,
        round(a.raw_average, 3)                                                             as raw_average,
        round(a.calibrated_average, 3)                                                      as calibrated_average,
        a.had_miscalibrated_interviewer,
        row_number() over (partition by f.requisition_id order by a.raw_average desc, f.application_id)        as raw_rank,
        row_number() over (partition by f.requisition_id order by a.calibrated_average desc, f.application_id) as calibrated_rank,
        o.offers_made,
        f.was_offered,
        f.was_hired
    from {{ ref('fct_application') }} f
    join averages a using (application_id)
    join offers_per_req o using (requisition_id)
)

select
    r.*,
    r.calibrated_rank <= r.offers_made and r.calibrated_average >= 3.0                     as in_calibrated_offer_list,
    r.was_offered <> (r.calibrated_rank <= r.offers_made and r.calibrated_average >= 3.0)  as offer_decision_changes,
    h.first_year_performance,
    h.stayed_12_months
from ranked r
left join {{ source('recruitment', 'hire_outcomes') }} h using (application_id)
