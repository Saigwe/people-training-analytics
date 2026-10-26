"""Export the gold reports and the attrition model to CSV for the Evidence.dev report (reports/sources/people).

The CSVs are small aggregates of the real-data run and are committed, so CI can build the report without the raw data.

Usage: python analysis/export_report_data.py --db warehouse/people.duckdb --model results/attrition_model.csv
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import duckdb

TABLES = ("rpt_training_cost_per_employee", "rpt_competency_gap_matrix", "rpt_attrition_by_training")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/people.duckdb")
    ap.add_argument("--model", type=Path, default=Path("results/attrition_model.csv"))
    ap.add_argument("--out", type=Path, default=Path("reports/sources/people"))
    args = ap.parse_args()
    con = duckdb.connect(args.db, read_only=True)
    for t in TABLES:
        path = args.out / f"{t.removeprefix('rpt_')}.csv"
        con.execute(f"copy (select * from gold.{t} order by all) to '{path.as_posix()}' (header)")
        print(f"{path}  {con.execute(f'select count(*) from gold.{t}').fetchone()[0]} rows")
    shutil.copy(args.model, args.out / "attrition_model.csv")
    print(args.out / "attrition_model.csv")


if __name__ == "__main__":
    main()
