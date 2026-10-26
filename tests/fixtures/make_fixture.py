"""Synthetic stand-ins for the three REAL bronze tables, so CI runs offline (fixed seed).

Same table and column names as ingestion/load.py writes: bronze.ibm_employees (600 made-up employees with IBM's 35
columns), bronze.onet_skills (35 skills x the 9 mapped occupations, IM and LV rows) and bronze.onet_occupations.
ingestion/generate_training.py then adds the synthetic dates and training history on top, exactly as for real data.

Usage: python tests/fixtures/make_fixture.py --db warehouse/fixture.duckdb --seed-file dbt/seeds/job_role_onet.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

SEED = 20
N = 600
ROLES = {"Sales Executive": ("Sales", 0.22), "Sales Representative": ("Sales", 0.06),
         "Healthcare Representative": ("Research & Development", 0.09), "Research Scientist": ("Research & Development", 0.2),
         "Laboratory Technician": ("Research & Development", 0.18), "Research Director": ("Research & Development", 0.05),
         "Manufacturing Director": ("Research & Development", 0.1), "Manager": ("Research & Development", 0.06),
         "Human Resources": ("Human Resources", 0.04)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/fixture.duckdb")
    ap.add_argument("--seed-file", type=Path, default=Path("dbt/seeds/job_role_onet.csv"))
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)
    con.execute("create schema if not exists bronze")

    role = rng.choice(list(ROLES), N, p=[v[1] for v in ROLES.values()])
    tenure = rng.integers(0, 25, N)
    trainings = rng.choice(7, N, p=[0.04, 0.05, 0.37, 0.33, 0.08, 0.08, 0.05])
    overtime = rng.random(N) < 0.28
    level = rng.integers(1, 6, N)
    income = (2000 + 3500 * level + rng.normal(0, 800, N)).clip(1009).round().astype(int)
    p_leave = 1 / (1 + np.exp(-(-1.6 + 1.6 * overtime - 0.18 * trainings - 0.3 * (level - 2))))
    emp = pd.DataFrame({
        "Age": rng.integers(18, 61, N), "Attrition": np.where(rng.random(N) < p_leave, "Yes", "No"),
        "BusinessTravel": rng.choice(["Travel_Rarely", "Travel_Frequently", "Non-Travel"], N, p=[0.71, 0.19, 0.1]),
        "DailyRate": rng.integers(100, 1500, N), "Department": [ROLES[r][0] for r in role],
        "DistanceFromHome": rng.integers(1, 30, N), "Education": rng.integers(1, 6, N),
        "EducationField": rng.choice(["Life Sciences", "Medical", "Marketing", "Technical Degree", "Other"], N),
        "EmployeeCount": 1, "EmployeeNumber": np.arange(1, N + 1) * 2,
        "EnvironmentSatisfaction": rng.integers(1, 5, N), "Gender": rng.choice(["Male", "Female"], N),
        "HourlyRate": rng.integers(30, 101, N), "JobInvolvement": rng.integers(1, 5, N), "JobLevel": level,
        "JobRole": role, "JobSatisfaction": rng.integers(1, 5, N),
        "MaritalStatus": rng.choice(["Single", "Married", "Divorced"], N), "MonthlyIncome": income,
        "MonthlyRate": rng.integers(2000, 27000, N), "NumCompaniesWorked": rng.integers(0, 10, N), "Over18": "Y",
        "OverTime": np.where(overtime, "Yes", "No"), "PercentSalaryHike": rng.integers(11, 26, N),
        "PerformanceRating": rng.choice([3, 4], N, p=[0.85, 0.15]), "RelationshipSatisfaction": rng.integers(1, 5, N),
        "StandardHours": 80, "StockOptionLevel": rng.integers(0, 4, N),
        "TotalWorkingYears": tenure + rng.integers(0, 15, N), "TrainingTimesLastYear": trainings,
        "WorkLifeBalance": rng.integers(1, 5, N), "YearsAtCompany": tenure,
        "YearsInCurrentRole": (tenure * rng.random(N)).astype(int),
        "YearsSinceLastPromotion": (tenure * rng.random(N) * 0.5).astype(int),
        "YearsWithCurrManager": (tenure * rng.random(N)).astype(int)})

    socs = pd.read_csv(args.seed_file).onet_soc_code
    skill_ids = [f"2.A.1.{c}" for c in "abcdef"] + [f"2.A.2.{c}" for c in "abcd"] + [f"2.B.1.{c}" for c in "abcdef"] \
        + [f"2.B.2.i"] + [f"2.B.3.{c}" for c in "abcdeghjklm"] + [f"2.B.4.{c}" for c in "egh"] + [f"2.B.5.{c}" for c in "abcd"]
    rows = []
    for soc in socs:
        for i, sid in enumerate(skill_ids):
            im = round(float(rng.uniform(1.5, 4.6)), 2)
            rows.append((soc, sid, f"Skill {i + 1:02d}", "IM", f"{im:.2f}", "n/a"))
            rows.append((soc, sid, f"Skill {i + 1:02d}", "LV", f"{min(7.0, im * rng.uniform(0.8, 1.3)):.2f}", "N"))
    skills = pd.DataFrame(rows, columns=["O*NET-SOC Code", "Element ID", "Element Name", "Scale ID", "Data Value",
                                         "Not Relevant"])
    skills["Recommend Suppress"] = "N"
    occupations = pd.DataFrame({"O*NET-SOC Code": socs, "Title": [f"Occupation {s}" for s in socs],
                                "Description": "synthetic"})
    for name, df in [("ibm_employees", emp), ("onet_skills", skills), ("onet_occupations", occupations)]:
        con.execute(f"create or replace table bronze.{name} as select * from df")
        print(f"bronze.{name:<17} {len(df):>6,} rows (fixture)")


if __name__ == "__main__":
    main()
