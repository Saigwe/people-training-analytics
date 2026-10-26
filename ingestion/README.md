# Ingestion

| Script | Writes | Kind |
|---|---|---|
| `load.py` | `bronze.ibm_employees`, `bronze.onet_skills`, `bronze.onet_occupations` | Real, unchanged |
| `generate_training.py` | `bronze.employee_dates`, `bronze.course_catalog`, `bronze.trainings` | Synthetic, fixed seed, anchored to the real IBM fields |

## Getting the real files
No account is needed. Save them under `data/raw/` (git-ignored):

```bash
mkdir -p data/raw/onet
curl -L -o data/raw/emp_attrition.csv https://raw.githubusercontent.com/IBM/employee-attrition-aif360/master/data/emp_attrition.csv
curl -L -o "data/raw/onet/Skills.txt" "https://www.onetcenter.org/dl_files/database/db_30_0_text/Skills.txt"
curl -L -o "data/raw/onet/Occupation Data.txt" "https://www.onetcenter.org/dl_files/database/db_30_0_text/Occupation%20Data.txt"
```

Then `make all`. CI doesn't download anything: `tests/fixtures/make_fixture.py` writes synthetic stand-ins with the same table and column names.
