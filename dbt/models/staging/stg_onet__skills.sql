-- REAL: O*NET skill ratings, one row per occupation and skill, with importance (1-5) and level (0-7) side by side.
select
    "O*NET-SOC Code"                                                              as onet_soc_code,
    "Element ID"                                                                  as skill_id,
    "Element Name"                                                                as skill,
    max(case when "Scale ID" = 'IM' then cast("Data Value" as double) end)        as importance,
    max(case when "Scale ID" = 'LV' then cast("Data Value" as double) end)        as required_level,
    bool_or("Scale ID" = 'LV' and "Not Relevant" = 'Y')                           as level_not_relevant
from {{ source('bronze', 'onet_skills') }}
group by 1, 2, 3
