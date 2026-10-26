# 3-minute walkthrough: People & Training Analytics

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** Evidence report, README, dbt/models, analysis/attrition_model.py, GitHub Actions.

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README title | Do people who train more stay longer? On IBM's 1,470-employee HR data, with 16 factors held equal, each extra training goes with 16% lower odds of leaving. |
| 0:20–0:45 | README intro and the Data section | I started my career as an HR analyst at a Nigerian electricity distributor, building training cost per employee and a technician competency matrix. This rebuilds it on IBM's public HR data and O*NET's skill requirements. No employer data is used. |
| 0:45–1:10 | The Evidence report at saigwe.github.io/reports/people-training | Cost per employee divides by everyone on payroll, not just the people who trained. |
| 1:10–1:35 | The competency-gap heatmap | Required levels are real, from O*NET. Achieved levels are a synthetic model written out in the SQL, and the report labels it. |
| 1:35–2:00 | `dbt/tests/assert_last_year_trainings_match_ibm.sql` | IBM has no course records, so the history is synthetic. It's anchored to the real data: each person's last-year completions equal IBM's count, and this test checks all 1,470. |
| 2:00–2:30 | The cohort table and odds ratios | With no training last year, 27.8% left, against 10.9% with five or six. The adjusted odds ratio is 0.84, with a 95% interval of 0.73 to 0.97, using real fields only. |
| 2:30–2:45 | `docs/design_doc.md`, the options table | The decision I'd defend in an interview: The model uses only real fields. Synthetic data appears only where public data has none, and every place it appears is labelled. |
| 2:45–3:00 | Back to the README top | For HR and L&D, that means cost per head, the skill gaps to close, and evidence about retention that's honest about its limits. The repo, numbers and design doc are linked under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- Run `make fixture-all` once before recording, so CI-style output is fresh if you show it.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- Say "synthetic" out loud wherever the README labels data as synthetic.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the roadmap line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
