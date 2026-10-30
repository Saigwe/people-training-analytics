-- Is each interviewer scoring on the same scale as their co-panellists? For every score, the offset is the score
-- minus the average the other two panellists gave the same candidate on the same competency, so candidate quality
-- cancels out. An interviewer is flagged when their average offset is at least half a point and its 95% confidence
-- interval excludes zero. SYNTHETIC (two miscalibrated interviewers are planted; the answer key is used only by tests).
with scored as (
    select
        s.*,
        (sum(s.score) over (partition by s.application_id, s.competency) - s.score)
            / (count(*) over (partition by s.application_id, s.competency) - 1)  as co_panel_average
    from {{ ref('stg_synthetic__interview_scores') }} s
),

offsets as (
    select interviewer_id, score - co_panel_average as offset_points
    from scored
)

select
    interviewer_id,
    count(*)                                                                as scores_given,
    round(avg(offset_points), 3)                                            as mean_offset,
    round(avg(offset_points) - 1.96 * stddev_samp(offset_points) / sqrt(count(*)), 3) as ci_low,
    round(avg(offset_points) + 1.96 * stddev_samp(offset_points) / sqrt(count(*)), 3) as ci_high,
    case
        when abs(avg(offset_points)) >= 0.5
         and sign(avg(offset_points) - 1.96 * stddev_samp(offset_points) / sqrt(count(*)))
           = sign(avg(offset_points) + 1.96 * stddev_samp(offset_points) / sqrt(count(*)))
        then case when avg(offset_points) > 0 then 'lenient' else 'harsh' end
        else 'calibrated'
    end                                                                     as calibration
from offsets
group by 1
