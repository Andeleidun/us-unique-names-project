#!/usr/bin/env bash
set -euo pipefail

DB="data/work/names.duckdb"
RELEASE="data/releases/2026-07-baseline"

python -m us_unique_names.cli init-db "$DB"

python -m us_unique_names.cli ingest-census-excel data/raw/census/Names2020_FirstNames_Sex.xlsx \
  --db "$DB" --source-id census_2020_first_names_by_sex --name-type first
python -m us_unique_names.cli ingest-census-excel data/raw/census/Names2020_LastNames_RaceHispanic.xlsx \
  --db "$DB" --source-id census_2020_last_names_race_hispanic --name-type last
python -m us_unique_names.cli ingest-census-zip data/raw/census/2010_names.zip \
  --db "$DB" --source-id census_2010_surnames --name-type last
python -m us_unique_names.cli ingest-census-zip data/raw/census/2000_names.zip \
  --db "$DB" --source-id census_2000_surnames --name-type last
python -m us_unique_names.cli ingest-ssa-national data/raw/ssa/names.zip \
  --db "$DB" --source-id ssa_national_baby_names
python -m us_unique_names.cli ingest-ssa-state data/raw/ssa/namesbystate.zip \
  --db "$DB" --source-id ssa_state_baby_names
python -m us_unique_names.cli ingest-ssa-state data/raw/ssa/namesbyterritory.zip \
  --db "$DB" --source-id ssa_territory_baby_names

python -m us_unique_names.cli export --db "$DB" --release-dir "$RELEASE"
python -m us_unique_names.cli validate-release "$RELEASE"
