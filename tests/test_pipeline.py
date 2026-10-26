"""Checks on a finished pipeline run (PEOPLE_DB, PEOPLE_RESULTS): the synthetic history is reproducible and the
model and reports are sane."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = os.environ.get("PEOPLE_DB", str(ROOT / "warehouse" / "fixture.duckdb"))
RESULTS = Path(os.environ.get("PEOPLE_RESULTS", ROOT / "data" / "fixture" / "results"))


def test_training_history_is_reproducible(tmp_path):
    db = tmp_path / "copy.duckdb"
    shutil.copy(DB, db)
    before = duckdb.connect(str(db)).execute("select count(*), sum(hash(employee_id, course_id, completed_on)) from bronze.trainings").fetchone()
    subprocess.run([sys.executable, str(ROOT / "ingestion" / "generate_training.py"), "--db", str(db),
                    "--seed-file", str(ROOT / "dbt" / "seeds" / "job_role_onet.csv")], check=True, capture_output=True)
    after = duckdb.connect(str(db)).execute("select count(*), sum(hash(employee_id, course_id, completed_on)) from bronze.trainings").fetchone()
    assert before == after


def test_only_leavers_have_exit_dates_and_they_fall_in_2025():
    con = duckdb.connect(DB, read_only=True)
    bad = con.execute("""select count(*) from gold.dim_employee
                         where (exit_date is not null) <> left_company or year(exit_date) <> 2025""").fetchone()[0]
    assert bad == 0


def test_gap_matrix_shares_are_proportions():
    con = duckdb.connect(DB, read_only=True)
    lo, hi = con.execute("""select min(least(share_meeting_requirement, share_trained_on_skill)),
                                   max(greatest(share_meeting_requirement, share_trained_on_skill))
                            from gold.rpt_competency_gap_matrix""").fetchone()
    assert 0 <= lo <= hi <= 1


def test_attrition_model_reports_the_training_odds_ratio():
    summary = json.loads((RESULTS / "attrition_model.json").read_text())
    adjusted = {r["term"]: r for r in summary["odds_ratios"] if r["model"] == "adjusted"}
    r = adjusted["Each extra training last year"]
    assert 0 < r["ci_low"] <= r["odds_ratio"] <= r["ci_high"]
