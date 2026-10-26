"""Does training predict staying? Logistic regression on the REAL IBM fields only (no synthetic data).

The raw cohort view (gold.rpt_attrition_by_training) shows attrition falling as training rises, but people who train more
may differ in other ways. This fits attrition on TrainingTimesLastYear with the usual controls and reports odds ratios
with 95% confidence intervals. It is an association in a cross-section, not a causal effect.

Usage: python analysis/attrition_model.py --db warehouse/people.duckdb --out results
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

CONTROLS = ("works_overtime + job_level + np.log(monthly_income) + age + years_at_company + years_since_last_promotion"
            " + num_companies_worked + distance_from_home_miles + stock_option_level + job_satisfaction"
            " + environment_satisfaction + work_life_balance + job_involvement + C(marital_status)"
            " + C(business_travel) + C(department)")
LABELS = {"training_times_last_year": "Each extra training last year", "works_overtime[T.True]": "Works overtime",
          "job_level": "Each job level up", "np.log(monthly_income)": "log(monthly income), per unit",
          "job_satisfaction": "Each point of job satisfaction (1-4)", "stock_option_level": "Each stock option level"}


def fit(df: pd.DataFrame, formula: str) -> pd.DataFrame:
    res = smf.logit(formula, df).fit(disp=False)
    ci = res.conf_int()
    return pd.DataFrame({"odds_ratio": np.exp(res.params), "ci_low": np.exp(ci[0]), "ci_high": np.exp(ci[1]),
                         "p_value": res.pvalues}).drop(index="Intercept"), res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/people.duckdb")
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args()
    df = duckdb.connect(args.db, read_only=True).execute("select * from gold.dim_employee").df()
    df["left"] = df.left_company.astype(int)

    raw, _ = fit(df, "left ~ training_times_last_year")
    adj, res = fit(df, f"left ~ training_times_last_year + {CONTROLS}")
    rows = [{"term": LABELS.get(t, t), "model": m, **{k: round(float(v), 4) for k, v in r.items()}}
            for m, tab in (("unadjusted", raw), ("adjusted", adj)) for t, r in tab.iterrows()
            if m == "unadjusted" or t in LABELS]
    summary = {"employees": len(df), "leavers": int(df.left.sum()), "pseudo_r2_adjusted": round(float(res.prsquared), 3),
               "odds_ratios": rows}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "attrition_model.json").write_text(json.dumps(summary, indent=2))
    pd.DataFrame(rows).to_csv(args.out / "attrition_model.csv", index=False)
    for r in rows:
        print(f"{r['model']:<11} {r['term']:<38} OR {r['odds_ratio']:.3f}  [{r['ci_low']:.3f}, {r['ci_high']:.3f}]"
              f"  p={r['p_value']:.4f}")
    print(f"employees {summary['employees']:,}, leavers {summary['leavers']}, pseudo R2 {summary['pseudo_r2_adjusted']}")


if __name__ == "__main__":
    main()
