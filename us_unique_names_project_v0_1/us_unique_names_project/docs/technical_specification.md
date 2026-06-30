# Technical Specification

## Release directory

```text
data/releases/YYYY-MM-DD/
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

## Public CSV schema

```csv
name
```

## Optional metadata schema

```csv
name,source_count,source_categories,confidence_tier
```

## Normalization

Canonical uniqueness uses:

1. Unicode NFC normalization.
2. Leading/trailing whitespace trim.
3. Repeated internal whitespace collapse.
4. Casefolded deduplication key.
5. Diacritics preserved.
6. Punctuation, hyphens, apostrophes, and compound surnames preserved.
7. No phonetic matching, stemming, transliteration, modernization, or correction.

## Validation

A release is valid only if:

- public files contain only the `name` column;
- names are deduplicated within each file;
- names are alphabetically sorted by normalized sort key;
- no emails, URLs, dates, phone numbers, IDs, titles, suffixes, ranks, organizations, or single-letter initials appear in the public files;
- checksums match;
- metadata is separate from canonical files.

## Pipeline

```text
source registry
  -> raw download
  -> source-specific extraction
  -> technical normalization
  -> public-name validation
  -> deduplication into first/last sets
  -> metadata aggregation
  -> CSV/Parquet/DuckDB export
  -> manifest and checksum generation
  -> release validation
```
