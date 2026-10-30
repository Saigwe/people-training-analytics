-- The calibration report must flag exactly the interviewers the generator miscalibrated, in the right direction,
-- and nobody else.
select c.interviewer_id, c.calibration, k.planted_bias
from {{ ref('rpt_interviewer_calibration') }} c
join {{ source('answer_key', 'interviewer_bias') }} k using (interviewer_id)
where (k.planted_bias > 0) <> (c.calibration = 'lenient')
   or (k.planted_bias < 0) <> (c.calibration = 'harsh')
