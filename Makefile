PY ?= python
DB ?= warehouse/people.duckdb
RESULTS ?= results
DBT_BIN ?= dbt
DBT = cd dbt && DUCKDB_PATH=../$(DB) $(DBT_BIN)

.PHONY: all load generate dbt model report-data test fixture-all clean

all: load generate dbt model report-data   ## real data: IBM + O*NET into bronze, synthetic history, dbt, model, report CSVs

load:       ## IBM attrition CSV and O*NET 30.0 text files, already in data/raw (see ingestion/README.md)
	$(PY) ingestion/load.py --raw data/raw --db $(DB)

generate:   ## SYNTHETIC employment dates, course catalogue and training history (fixed seed)
	$(PY) ingestion/generate_training.py --db $(DB)

dbt:
	$(DBT) deps --profiles-dir .
	$(DBT) build --profiles-dir .

model:      ## logistic regression on the real IBM fields
	$(PY) analysis/attrition_model.py --db $(DB) --out $(RESULTS)

report-data:   ## gold reports -> reports/sources/people/*.csv for Evidence.dev
	$(PY) analysis/export_report_data.py --db $(DB) --model $(RESULTS)/attrition_model.csv

test:
	PEOPLE_DB=$(DB) PEOPLE_RESULTS=$(RESULTS) $(PY) -m pytest -q tests

fixture-all:   ## synthetic stand-ins for IBM and O*NET, offline: generate, dbt, model, tests (CI)
	$(PY) tests/fixtures/make_fixture.py --db warehouse/fixture.duckdb
	$(MAKE) generate dbt DB=warehouse/fixture.duckdb
	$(MAKE) model test DB=warehouse/fixture.duckdb RESULTS=data/fixture/results

clean:
	rm -rf warehouse dbt/target dbt/logs data/fixture
