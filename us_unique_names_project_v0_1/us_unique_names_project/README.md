# U.S. Unique First and Last Name Sets

This project builds privacy-preserving, durable sets of unique first-name and last-name spellings found in approved U.S. jurisdictional and founding-era historical sources.

The canonical public output contains only one-column name files:

```text
first_names.csv
last_names.csv
```

Each spelling is included once per set. Diacritics, punctuation, transliterations, and historical spelling variants are preserved. Full names and identifying context are never published.

## v0.1 scope

The initial executable package targets high-structure sources only:

- 2020 Census first-name table
- 2020 Census last-name table
- 2010 Census surname table
- SSA national baby-name data
- Optional SSA state and territory baby-name files

The package includes ingestion scripts, a source registry, validation checks, release schema, and project documentation.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/download_sources.py --sources config/sources.v0.1.yaml --raw-dir data/raw
python scripts/build_release.py --sources config/sources.v0.1.yaml --raw-dir data/raw --release-dir data/releases/v0.1
python scripts/validate_release.py data/releases/v0.1
```

## Privacy rules

The public files contain names only. The pipeline rejects full-name pairs, record identifiers, addresses, dates, source row IDs, occupations, employers, military units, and other identifying context.

## Release files

A completed release directory contains:

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
```
