"""SYNTHETIC employment dates and training history, anchored to the real IBM fields (fixed seed).

IBM's file is a single snapshot: it has tenure (YearsAtCompany), the number of trainings last year
(TrainingTimesLastYear) and whether the employee left (Attrition), but no dates or course records. This script adds:

  bronze.employee_dates   hire date (from real tenure) and, for leavers, an exit date in 2025; snapshot 31 Dec 2025
  bronze.course_catalog   one course per O*NET skill, in three formats with cost and hours:
                            e-learning (50%): GBP 80-200, 2-4 h · classroom (35%): GBP 600-1,200, 7-14 h
                            certification (15%): GBP 1,500-3,000, 21-40 h
  bronze.trainings        completions 2021-2025 while employed. The LAST year matches the real TrainingTimesLastYear
                          exactly (tested); earlier years are Poisson around the same rate. 70% of courses target the
                          skills O*NET rates most important for the employee's occupation, 30% are general.

Usage: python ingestion/generate_training.py --db warehouse/people.duckdb --seed-file dbt/seeds/job_role_onet.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

SEED = 2020
SNAPSHOT = pd.Timestamp("2025-12-31")
FIRST_YEAR, LAST_YEAR = 2021, 2025
FORMATS = {"e-learning": (0.50, (80, 200), (2, 4)), "classroom": (0.35, (600, 1200), (7, 14)),
           "certification": (0.15, (1500, 3000), (21, 40))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/people.duckdb")
    ap.add_argument("--seed-file", type=Path, default=Path("dbt/seeds/job_role_onet.csv"))
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)
    con = duckdb.connect(args.db)
    emp = con.execute("""select EmployeeNumber as employee_id, JobRole as job_role, YearsAtCompany as tenure,
                                TrainingTimesLastYear as last_year_trainings, Attrition = 'Yes' as left_company
                         from bronze.ibm_employees order by EmployeeNumber""").df()
    roles = pd.read_csv(args.seed_file)
    skills = con.execute("""select "O*NET-SOC Code" as soc, "Element ID" as skill_id, "Element Name" as skill,
                                   cast("Data Value" as double) as importance
                            from bronze.onet_skills where "Scale ID" = 'IM'""").df()

    # employment dates
    n = len(emp)
    exit_date = pd.Series(pd.NaT, index=emp.index)
    leavers = emp.left_company.to_numpy()
    exit_date[leavers] = pd.Timestamp("2025-01-15") + pd.to_timedelta(rng.integers(0, 335, leavers.sum()), unit="D")
    end = exit_date.fillna(SNAPSHOT)
    hire = end - pd.to_timedelta((emp.tenure * 365.25).round().astype(int) + rng.integers(0, 365, n), unit="D")
    dates = pd.DataFrame({"employee_id": emp.employee_id, "hire_date": hire.dt.date, "exit_date": exit_date.dt.date})

    # course catalogue: one course per O*NET skill
    all_skills = skills.drop_duplicates("skill_id")[["skill_id", "skill"]].sort_values("skill_id").reset_index(drop=True)
    fmt = rng.choice(list(FORMATS), len(all_skills), p=[v[0] for v in FORMATS.values()])
    catalog = all_skills.assign(
        course_id=[f"C{i + 1:03d}" for i in range(len(all_skills))], format=fmt,
        course_name=[f"{s} ({f})" for s, f in zip(all_skills.skill, fmt)],
        cost_gbp=[int(rng.integers(*FORMATS[f][1])) for f in fmt],
        hours=[int(rng.integers(FORMATS[f][2][0], FORMATS[f][2][1] + 1)) for f in fmt])

    # training completions
    soc_of = dict(zip(roles.job_role, roles.onet_soc_code))
    important = {soc: g[g.importance >= 3.0].sort_values("importance", ascending=False)
                 for soc, g in skills.groupby("soc")}
    course_of_skill = dict(zip(catalog.skill_id, catalog.course_id))
    rows = []
    for e, h, x in zip(emp.itertuples(), hire, end):
        for year in range(FIRST_YEAR, LAST_YEAR + 1):
            start, stop = max(h, pd.Timestamp(f"{year}-01-01")), min(x, pd.Timestamp(f"{year}-12-31"))
            if start > stop:
                continue
            last = year == LAST_YEAR if not e.left_company else year == x.year
            count = int(e.last_year_trainings) if last else int(rng.poisson(0.7 * e.last_year_trainings + 0.6))
            pool = important.get(soc_of.get(e.job_role))
            for _ in range(count):
                if pool is not None and len(pool) and rng.random() < 0.7:
                    skill_id = pool.skill_id.iloc[int(rng.choice(len(pool), p=(pool.importance / pool.importance.sum()).to_numpy()))]
                else:
                    skill_id = all_skills.skill_id.iloc[int(rng.integers(len(all_skills)))]
                day = start + pd.Timedelta(days=int(rng.integers(0, (stop - start).days + 1)))
                rows.append((e.employee_id, course_of_skill[skill_id], day.date()))
    trainings = pd.DataFrame(rows, columns=["employee_id", "course_id", "completed_on"])
    trainings.insert(0, "training_id", [f"T{i:06d}" for i in range(len(trainings))])

    for name, df in [("employee_dates", dates), ("course_catalog", catalog), ("trainings", trainings)]:
        con.execute(f"create or replace table bronze.{name} as select * from df")
        print(f"bronze.{name:<16} {len(df):>7,} rows (synthetic)")


if __name__ == "__main__":
    main()
