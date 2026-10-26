"""Load the real sources into DuckDB `bronze`, unchanged.

  bronze.ibm_employees   IBM HR Analytics Employee Attrition (1,470 employees, 35 columns), from IBM's own repo:
                         https://github.com/IBM/employee-attrition-aif360 (data/emp_attrition.csv). It is a
                         fictional dataset IBM created for teaching; no real person is described.
  bronze.onet_skills     O*NET 30.0 Skills (importance IM and level LV per occupation and skill), CC BY 4.0
  bronze.onet_occupations  O*NET 30.0 occupation titles

Usage: python ingestion/load.py --raw data/raw --db warehouse/people.duckdb
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--db", default="warehouse/people.duckdb")
    args = ap.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)
    con.execute("create schema if not exists bronze")
    ibm = (args.raw / "emp_attrition.csv").as_posix()
    onet = args.raw / "onet"
    con.execute(f"create or replace table bronze.ibm_employees as select * from read_csv('{ibm}', header = true)")
    con.execute(f"""create or replace table bronze.onet_skills as
        select * from read_csv('{(onet / "Skills.txt").as_posix()}', delim = '\t', header = true, all_varchar = true)""")
    con.execute(f"""create or replace table bronze.onet_occupations as
        select * from read_csv('{(onet / "Occupation Data.txt").as_posix()}', delim = '\t', header = true, all_varchar = true)""")
    for t in ("ibm_employees", "onet_skills", "onet_occupations"):
        print(f"bronze.{t:<18} {con.execute(f'select count(*) from bronze.{t}').fetchone()[0]:>7,} rows")


if __name__ == "__main__":
    main()
