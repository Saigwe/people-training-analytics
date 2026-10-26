---
title: People & Training Analytics
---

Training cost, competency gaps and attrition for 1,470 employees. **Employee attributes and attrition are real** (IBM HR
Analytics, a fictional teaching dataset) and **required competencies are real** (O*NET 30.0). Course records, costs and
achieved competency levels are **synthetic**: IBM's file has no course history. Source:
[github.com/Saigwe/people-training-analytics](https://github.com/Saigwe/people-training-analytics).

```sql headline
select
    sum(training_cost_gbp) filter (where training_year = 2025) as cost_2025,
    sum(training_cost_gbp) filter (where training_year = 2025)
        / sum(employees_on_payroll) filter (where training_year = 2025) as cost_per_employee_2025
from people.training_cost_per_employee
```

```sql attrition_all
select * from people.attrition_by_training where department = 'All' order by training_band
```

```sql training_or
select odds_ratio, ci_low, ci_high from people.attrition_model
where model = 'adjusted' and term = 'Each extra training last year'
```

<BigValue data={headline} value=cost_2025 title="Training spend 2025 (synthetic)" fmt=gbp0 />
<BigValue data={headline} value=cost_per_employee_2025 title="Per employee on payroll, 2025 (synthetic)" fmt=gbp0 />
<BigValue data={attrition_all} value=attrition_rate title="Attrition, 0 trainings last year (real)" fmt=pct1 />
<BigValue data={training_or} value=odds_ratio title="Odds of leaving per extra training, adjusted (real)" fmt=num2 />

## Training cost per employee

Spend divided by everyone on payroll at any point in the year, including people who trained nothing. Synthetic.

```sql cost
select cast(cast(training_year as integer) as varchar) as year, department, cost_per_employee_gbp, hours_per_employee, employees_on_payroll,
       employees_trained, trainings, training_cost_gbp
from people.training_cost_per_employee
order by training_year, department
```

<BarChart data={cost} x=year y=cost_per_employee_gbp series=department type=grouped sort=false yFmt=gbp0
          title="Cost per employee by year and department" />

<DataTable data={cost} rows=15>
  <Column id=year />
  <Column id=department />
  <Column id=employees_on_payroll title="On payroll" />
  <Column id=employees_trained title="Trained" />
  <Column id=trainings />
  <Column id=training_cost_gbp title="Spend" fmt=gbp0 />
  <Column id=cost_per_employee_gbp title="Per employee" fmt=gbp0 />
  <Column id=hours_per_employee title="Hours per employee" fmt=num1 />
</DataTable>

## Competency-gap matrix

For each job role, the 8 skills O*NET rates most important for its occupation, with the level required (real, 0-7
scale). The achieved level is a synthetic model of job level, experience, performance rating and courses completed on
that skill, for the 1,233 employees on payroll at 31 Dec 2025.

```sql gaps
select job_role, skill, required_level, avg_achieved_level, avg_gap, share_meeting_requirement, share_trained_on_skill,
       employees
from people.competency_gap_matrix
order by job_role, skill_rank
```

```sql role_gaps
select job_role, avg(avg_gap) as avg_gap, avg(share_meeting_requirement) as share_meeting_requirement,
       max(employees) as employees
from people.competency_gap_matrix
group by job_role
order by avg_gap desc
```

<Heatmap data={gaps} x=skill y=job_role value=avg_gap valueFmt=num2 title="Average gap to required level (levels)" />

<BarChart data={role_gaps} x=job_role y=share_meeting_requirement swapXY=true yFmt=pct0
          title="Share of skill requirements met, by role" />

<DataTable data={gaps} search=true rows=16>
  <Column id=job_role />
  <Column id=skill />
  <Column id=required_level title="Required" fmt=num2 />
  <Column id=avg_achieved_level title="Achieved (avg)" fmt=num2 />
  <Column id=avg_gap title="Gap" fmt=num2 contentType=colorscale />
  <Column id=share_meeting_requirement title="Meeting requirement" fmt=pct0 />
  <Column id=share_trained_on_skill title="Trained on skill" fmt=pct0 />
</DataTable>

## Attrition cohorts: trained vs not trained

Real data. IBM records how many trainings each employee had last year and whether they left.

```sql cohorts
select department, training_band, employees, leavers, attrition_rate
from people.attrition_by_training
order by department, training_band
```

<BarChart data={cohorts} x=training_band y=attrition_rate series=department type=grouped sort=false yFmt=pct0
          title="Attrition rate by trainings last year" />

<DataTable data={cohorts} rows=16>
  <Column id=department />
  <Column id=training_band title="Trainings last year" />
  <Column id=employees />
  <Column id=leavers />
  <Column id=attrition_rate title="Attrition" fmt=pct1 />
</DataTable>

### Holding other factors equal

People who train more may differ in other ways, so a logistic regression adds overtime, job level, income, age, tenure,
time since promotion, prior employers, commute, stock options, satisfaction scores, marital status, travel and
department. The odds ratios below are associations in a single snapshot, not proof that training causes people to stay.

```sql model
select model, term, odds_ratio, ci_low, ci_high, p_value from people.attrition_model order by model desc, odds_ratio
```

<DataTable data={model}>
  <Column id=model />
  <Column id=term />
  <Column id=odds_ratio title="Odds ratio" fmt=num3 />
  <Column id=ci_low title="95% CI low" fmt=num3 />
  <Column id=ci_high title="95% CI high" fmt=num3 />
  <Column id=p_value title="p" fmt=num4 />
</DataTable>
