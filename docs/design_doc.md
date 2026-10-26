# Design doc: People & Training Analytics

| | |
|---|---|
| **Author** | Stanley Igwe |
| **Status** | Built |
| **Last updated** | 26 Oct 2026 |

## 1. Problem and users
- **Users:** the Head of L&D, HR business partners and the finance partner who signs off the training budget.
- **Questions they need answered:** What do we spend on training per employee, by department and year? Which roles are furthest from the skill levels the job needs? Do people who train more stay longer, once other factors are held equal?
- **Current pain (scenario):** the budget review asks for cost per head. L&D divides spend by the number of people who trained, which flatters the figure, and can't say which gaps the money closed or whether it helped retention.

## 2. Requirements
| Type | Requirement |
|---|---|
| Functional | Cost per employee by year and department; a role × skill gap matrix; attrition by training band; an adjusted estimate with confidence intervals; a shareable report |
| Data quality | Every role maps to an O*NET occupation; no completion outside employment; the synthetic history matches IBM's real training counts exactly; every report has a tested grain |
| Freshness / SLA | Monthly, after the HR and LMS extracts land. A full rebuild takes 17 s, so no incremental logic |
| Scale | 1,470 employees and 16,520 completions today. Design target: 15,000 employees and 1M completions, still one DuckDB file |
| Cost | £0: DuckDB locally, GitHub Actions and Pages for CI and the report |

## 3. Design
- **Layers:** bronze (raw, unchanged) → silver (typed, keys tested) → gold (dimension, fact and reports).
- **Key choices:**
  - **Real where it exists, synthetic where it doesn't, and labelled everywhere.** IBM gives real attrition and a real training count; O*NET gives real skill requirements. Course records and achieved levels don't exist publicly, so they're generated and named `synthetic` in the sources, SQL comments, README and report.
  - **Anchor the synthetic data and test the anchor.** The 2025 completions equal IBM's `TrainingTimesLastYear` for all 1,470 people (`assert_last_year_trainings_match_ibm`), tenure sets hire dates, and only real leavers exit. That's why the synthetic cost and gap views stay consistent with the real attrition view.
  - **The model uses real fields only.** The odds ratio doesn't depend on anything I generated.
  - **Cost per employee divides by everyone on payroll at any point in the year**, so people who trained nothing, and leavers, count.
  - **Gap model in SQL, in the open.** The achieved-level formula is written in `rpt_competency_gap_matrix.sql`, so a reviewer can see what drives the matrix and replace it with real assessment data later.
  - **Evidence reads committed CSV exports.** CI builds the report without the raw files; the portfolio site serves the built pages.

## 4. Options considered
| Decision | Options | Chosen | Why |
|---|---|---|---|
| Competency framework | Make up a skills list; ESCO; O*NET | O*NET 30.0 | Public, CC BY 4.0, gives both importance and required level per occupation |
| Role mapping | Automatic title match; hand mapping | Hand mapping as a dbt seed, with reasons | Only 9 roles; a reviewer can challenge each line |
| Training effect | Raw cohort rates; logistic regression; propensity matching | Cohort rates plus logistic regression | Rates for the business, odds ratios with CIs for rigour; 237 leavers is too few for matching to add much |
| Report tool | Streamlit; Power BI; Evidence.dev | Evidence.dev | SQL and Markdown in git, builds to a static site, no server |
| Report data | Query DuckDB in CI; committed CSV exports | CSV exports | The raw files aren't in the repo; the exports are small aggregates |

## 5. Risks and what I'd change at 10x scale
- **Synthetic parts can mislead.** The cost and gap numbers describe a made-up history. With a real LMS extract, replace `bronze.trainings` and `course_catalog`; the models and tests stay the same.
- **Reverse causation.** People planning to leave may skip training, which would produce the same odds ratio. With real dated records I'd use training before a fixed window and attrition after it.
- **One snapshot.** IBM has no history, so there's no trend in attrition. A monthly HR snapshot would allow survival analysis (time to exit by training exposure).
- **At 10x:** the same design holds. I'd add incremental models for completions, partition the fact by year, and replace the hand mapping with a maintained job-architecture table.
