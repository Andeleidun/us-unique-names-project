# Implementation Roadmap

## Now: v0.1 baseline scaffold

1. Register baseline sources in `config/sources.yaml`.
2. Initialize the DuckDB schema from `schemas/names.sql`.
3. Ingest only aggregate Census and SSA sources.
4. Validate candidate names before writing canonical names.
5. Export one-column public CSV and Parquet files.
6. Generate `manifest.json` and `checksums.sha256`.
7. Run release validation before publication.

## v0.1 release criteria

- `first_names.csv` and `last_names.csv` each contain exactly one column: `name`.
- Every public name has at least one accepted source assertion.
- Review, rejected, and pending candidates are excluded from public files.
- No emails, URLs, phone numbers, dates, record IDs, titles, suffixes, ranks, organization markers, or single-letter first-name initials appear in public outputs.
- Checksums match every exported artifact.

## Next: v0.2 NPPES pilot

NPPES should be the first modern structured expansion after v0.1. The extractor must prove it never persists NPI numbers, addresses, taxonomy, phone numbers, endpoints, or practice locations.

## Later: historical pilots

Run one historical source pilot at a time. Recommended order:

1. Freedmen's Bureau structured indexed fields
2. Passenger arrival indexes from U.S.-created records
3. Military service and pension indexes
4. Court, probate, church, and newspaper OCR sources only after review throughput is known

## Deferred sources

FEC individual contribution records require legal review before use. Social-platform scraping is excluded.
