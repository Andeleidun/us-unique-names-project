# U.S. Unique First and Last Name Sets

This repository is the execution scaffold for a privacy-preserving project that produces two canonical public files:

- `first_names.csv`
- `last_names.csv`

Each public file contains exactly one column, `name`. No full names, person records, locations, dates, URLs, IDs, occupations, employers, household relationships, or other identifying context are exported.

## v0.1 goal

Build a safe baseline release from high-structure aggregate sources:

1. 2020 Census first names
2. 2020 Census last names
3. 2010 Census surnames
4. 2000 Census surnames
5. 1990 Census names, where useful as a structured historical comparison
6. SSA national baby names
7. SSA state baby names
8. SSA territory baby names

The source registry is in `config/sources.yaml`.

## Important retention rule

Raw source files may be downloaded into `data/raw/`, but public outputs must contain only deduplicated name strings and safe metadata. For person-level future sources, extractors must stream only approved name fields and discard all other fields immediately.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Initialize the database

```bash
python -m us_unique_names.cli init-db data/work/names.duckdb
```

## Download source files

Use the official URLs in `config/sources.yaml`. Place files under `data/raw/`, for example:

```text
data/raw/census/Names2020_FirstNames_Sex.xlsx
data/raw/census/Names2020_LastNames_RaceHispanic.xlsx
data/raw/census/2010_names.zip
data/raw/census/2000_names.zip
data/raw/ssa/names.zip
data/raw/ssa/namesbystate.zip
data/raw/ssa/namesbyterritory.zip
```

This scaffold intentionally does not scrape social platforms and does not ingest person-level sources in v0.1.

## Ingest examples

```bash
python -m us_unique_names.cli ingest-ssa-national \
  data/raw/ssa/names.zip \
  --db data/work/names.duckdb \
  --source-id ssa_national_baby_names

python -m us_unique_names.cli ingest-ssa-state \
  data/raw/ssa/namesbystate.zip \
  --db data/work/names.duckdb \
  --source-id ssa_state_baby_names

python -m us_unique_names.cli ingest-census-zip \
  data/raw/census/2010_names.zip \
  --db data/work/names.duckdb \
  --source-id census_2010_surnames \
  --name-type last

python -m us_unique_names.cli ingest-census-excel \
  data/raw/census/Names2020_FirstNames_Sex.xlsx \
  --db data/work/names.duckdb \
  --source-id census_2020_first_names_by_sex \
  --name-type first
```

## Export a release

```bash
python -m us_unique_names.cli export \
  --db data/work/names.duckdb \
  --release-dir data/releases/2026-07-baseline

python -m us_unique_names.cli validate-release data/releases/2026-07-baseline
```

## Run tests

```bash
python -m pytest
```

## Release contents

A successful release directory contains:

```text
first_names.csv
last_names.csv
first_names.parquet
last_names.parquet
first_name_metadata.csv
last_name_metadata.csv
names.duckdb
manifest.json
checksums.sha256
sources.yaml
release_notes.md
```
