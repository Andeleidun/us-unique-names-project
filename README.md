# U.S. Unique First and Last Name Sets

This repository is the execution scaffold for a privacy-preserving project that produces two canonical public files:

- `first_names.csv`
- `last_names.csv`

Each public file contains exactly one column, `name`. No full names, person records, locations, dates, URLs, IDs, occupations, employers, household relationships, or other identifying context are exported.

## v0.1 goal

Build a precision-first baseline release from high-structure aggregate sources enabled in `config/sources.yaml`:

1. 2020 Census first names
2. 2020 Census last names
3. 2010 Census surnames
4. SSA national baby names

Optional configured sources are disabled until explicitly enabled: Census 1990, Census 2000, SSA state, SSA territory, and the NPPES pilot metadata.

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

Download enabled sources from the registry when you intentionally want raw source files:

```bash
python -m us_unique_names.cli download-sources --sources config/sources.yaml --raw-dir data/raw
```

The standalone `scripts/download_sources.py` wrapper calls the same package implementation.
Existing raw files are skipped by default. Pass `--force` to re-download them or `--continue-on-error` to keep going after a source download fails.

This scaffold intentionally does not scrape social platforms and does not ingest person-level sources in v0.1.

## Ingest examples

The preferred ingestion interface uses the parser configured in `config/sources.yaml`:

```bash
python -m us_unique_names.cli ingest-source \
  --db data/work/names.duckdb \
  --source-id ssa_national_baby_names
```

When `--path` is omitted, `ingest-source` reads the configured `file_name` from `--raw-dir`:

```text
data/raw/ssa_names_national.zip
```

Source-specific commands remain available for direct extractor testing and troubleshooting:

```bash
python -m us_unique_names.cli ingest-ssa-national \
  data/raw/ssa_names_national.zip \
  --db data/work/names.duckdb \
  --source-id ssa_national_baby_names

python -m us_unique_names.cli ingest-census-zip \
  data/raw/census_2010_surnames.zip \
  --db data/work/names.duckdb \
  --source-id census_2010_surnames \
  --name-type last

python -m us_unique_names.cli ingest-census-excel \
  data/raw/Names2020_FirstNames_Sex.xlsx \
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

## Build a baseline

The orchestration command downloads enabled sources, initializes the database, checks expected source row counts, ingests sources, exports a release, validates it, and writes `build_notes.json` plus `release_coverage.json`.

```bash
python -m us_unique_names.cli build-baseline \
  --db data/work/baseline.duckdb \
  --release-dir data/releases/2026-07-baseline \
  --overwrite-db
```

If SSA blocks automated ZIP downloads, place the extracted national SSA files in `names/` and pass a source override:

```bash
python -m us_unique_names.cli build-baseline \
  --db data/work/baseline.duckdb \
  --release-dir data/releases/2026-07-baseline \
  --overwrite-db \
  --source-path ssa_national_baby_names=names
```

Inspect source coverage for a database or release:

```bash
python -m us_unique_names.cli source-status \
  --db data/work/baseline.duckdb \
  --release-dir data/releases/2026-07-baseline
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
build_notes.json
release_coverage.json
```
