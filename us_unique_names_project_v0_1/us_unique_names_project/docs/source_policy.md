# Source Policy

## Approved v0.1 sources

Use structured aggregate sources first:

- Census aggregate first-name and last-name tables
- Census surname tables
- SSA baby-name tables

## Later approved categories

Add only with source-specific extraction rules:

- NPPES/NPI individual provider fields
- U.S. passenger arrival indexes
- U.S. naturalization records
- U.S. military records
- Freedmen's Bureau and Freedman's Bank indexes
- Wikidata structured given-name and family-name properties
- ORCID public data, if U.S. scope can be controlled

## Disallowed by default

- Scraping Facebook or LinkedIn
- Foreign civil records not created under U.S. jurisdiction
- Person-level raw data in public release
- Full-name pairs
- Location, date, record, relationship, employer, profile, or ID fields
