"""SYNTHETIC recruitment funnel and structured interview scores, with planted problems and an answer key (fixed seed).

There is no open dataset of applications and interview scores, so this follows the repo's rule for synthetic data:
every planted effect is written to the answer_key schema, and the dbt models must find it without reading it.

  bronze.requisitions        30 requisitions in 2024-2025 for the IBM job roles, including one mass-hiring
                             campaign for 220 sales representatives
  bronze.applications        one row per applicant: requisition, source channel, applied date
  bronze.application_events  the stages each applicant reached, with dates:
                             applied > screened > assessed > interviewed > offered > accepted > started
  bronze.interview_scores    structured panel interviews: 3 interviewers per candidate, 4 competencies scored 1-5
                             against a rubric
  bronze.hire_outcomes       for each starter: first-year performance rating (1-5) and whether they stayed 12 months

Planted (answer_key.interviewer_bias): two of the 14 interviewers are miscalibrated, one lenient (+0.9 points) and
one harsh (-0.8 points). Offers are made on raw panel averages, as the business did, so their bias changes who gets
an offer. Each applicant has a latent ability that drives the assessment, the interview and first-year performance,
so the models can test whether calibrating the scores predicts performance better.

Usage: python ingestion/generate_recruitment.py --db warehouse/people.duckdb
"""
from __future__ import annotations

import argparse

import duckdb
import numpy as np
import pandas as pd

SEED = 2014
SOURCES = {  # share of applicants, mean latent ability
    "job board": (0.40, -0.15), "careers site": (0.25, 0.0), "referral": (0.15, 0.35),
    "agency": (0.12, 0.10), "campus": (0.08, -0.05),
}
STAGES = ["applied", "screened", "assessed", "interviewed", "offered", "accepted", "started"]
COMPETENCIES = ["communication", "problem solving", "customer focus", "integrity and safety"]
INTERVIEWERS = [f"I{i:02d}" for i in range(1, 15)]
BIAS = {"I07": 0.9, "I11": -0.8}
ROLES = {  # role: (requisitions, openings per requisition, applicants per opening)
    "Sales Representative": (1, 220, 9),
    "Sales Executive": (4, 6, 18), "Laboratory Technician": (5, 5, 16), "Research Scientist": (5, 4, 20),
    "Healthcare Representative": (3, 4, 15), "Manufacturing Director": (3, 1, 30), "Manager": (3, 1, 35),
    "Human Resources": (3, 2, 22), "Research Director": (3, 1, 28),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/people.duckdb")
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)

    reqs, apps, events, scores, outcomes = [], [], [], [], []
    req_no = 0
    for role, (n_req, openings, per_opening) in ROLES.items():
        for _ in range(n_req):
            req_no += 1
            req_id = f"R{req_no:03d}"
            opened = pd.Timestamp("2024-01-08") + pd.Timedelta(days=int(rng.integers(0, 600)))
            reqs.append({"requisition_id": req_id, "job_role": role, "openings": openings, "opened_on": opened.date()})
            n_app = int(openings * per_opening * rng.uniform(0.85, 1.15))
            src_names = list(SOURCES)
            src = rng.choice(src_names, n_app, p=[SOURCES[s][0] for s in src_names])
            ability = rng.normal([SOURCES[s][1] for s in src], 1.0)
            applied = opened + pd.to_timedelta(rng.integers(0, 28, n_app), unit="D")
            cands = []
            for k in range(n_app):
                app_id = f"{req_id}-A{k + 1:04d}"
                apps.append({"application_id": app_id, "requisition_id": req_id, "source_channel": src[k],
                             "applied_on": applied[k].date()})
                day = applied[k]
                events.append({"application_id": app_id, "stage": "applied", "stage_date": day.date()})
                if rng.random() > 1 / (1 + np.exp(-(0.4 + 0.9 * ability[k]))):  # CV screen
                    continue
                day += pd.Timedelta(days=int(rng.integers(2, 8)))
                events.append({"application_id": app_id, "stage": "screened", "stage_date": day.date()})
                assessment = ability[k] + rng.normal(0, 0.7)
                if assessment < -0.2:                                            # aptitude test
                    continue
                day += pd.Timedelta(days=int(rng.integers(3, 10)))
                events.append({"application_id": app_id, "stage": "assessed", "stage_date": day.date()})
                if rng.random() < 0.15:                                          # withdrew before interview
                    continue
                day += pd.Timedelta(days=int(rng.integers(4, 15)))
                events.append({"application_id": app_id, "stage": "interviewed", "stage_date": day.date()})
                panel = rng.choice(INTERVIEWERS, 3, replace=False)
                total = 0.0
                for iv in panel:
                    for comp in COMPETENCIES:
                        raw = 3 + 0.8 * ability[k] + BIAS.get(iv, 0.0) + rng.normal(0, 0.6)
                        s = int(np.clip(np.rint(raw), 1, 5))
                        total += s
                        scores.append({"application_id": app_id, "interviewer_id": iv, "competency": comp,
                                       "score": s, "interviewed_on": day.date()})
                cands.append((app_id, total / (3 * len(COMPETENCIES)), day, ability[k]))
            # Offers on the raw panel average, as the business did: best first, up to the openings, if 3.0 or above.
            cands.sort(key=lambda c: -c[1])
            for app_id, avg, day, ab in cands[: int(openings * 1.15)]:
                if avg < 3.0:
                    break
                day += pd.Timedelta(days=int(rng.integers(2, 7)))
                events.append({"application_id": app_id, "stage": "offered", "stage_date": day.date()})
                if rng.random() < 0.18:                                          # declined
                    continue
                day += pd.Timedelta(days=int(rng.integers(1, 6)))
                events.append({"application_id": app_id, "stage": "accepted", "stage_date": day.date()})
                if rng.random() < 0.05:                                          # no-show
                    continue
                day += pd.Timedelta(days=int(rng.integers(14, 35)))
                events.append({"application_id": app_id, "stage": "started", "stage_date": day.date()})
                perf = int(np.clip(np.rint(3 + 0.6 * ab + rng.normal(0, 0.7)), 1, 5))
                stayed = rng.random() < 1 / (1 + np.exp(-(1.4 + 0.7 * ab)))
                outcomes.append({"application_id": app_id, "first_year_performance": perf, "stayed_12_months": bool(stayed)})

    tables = {"requisitions": pd.DataFrame(reqs), "applications": pd.DataFrame(apps),
              "application_events": pd.DataFrame(events), "interview_scores": pd.DataFrame(scores),
              "hire_outcomes": pd.DataFrame(outcomes)}
    key = pd.DataFrame([{"interviewer_id": i, "planted_bias": BIAS.get(i, 0.0),
                         "is_miscalibrated": i in BIAS} for i in INTERVIEWERS])
    con = duckdb.connect(args.db)
    con.execute("create schema if not exists bronze")
    con.execute("create schema if not exists answer_key")
    for name, df in tables.items():
        con.register("df", df)
        con.execute(f"create or replace table bronze.{name} as select * from df")
        con.unregister("df")
        print(f"bronze.{name:<20} {len(df):>8,} rows")
    con.register("df", key)
    con.execute("create or replace table answer_key.interviewer_bias as select * from df")
    con.unregister("df")


if __name__ == "__main__":
    main()
