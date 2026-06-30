# Research Brief: U.S. Unique First and Last Name Sets

## Purpose

Create durable, privacy-preserving datasets of unique first-name and last-name spellings found in approved U.S. jurisdictional and founding-era historical sources.

The canonical public release consists of:

```text
first_names.csv
last_names.csv
```

Each file contains exactly one public column:

```csv
name
```

## Scope

- Include colonial-era records before 1776 when clearly connected to the founding-era United States.
- Use strict U.S. jurisdictional scope for post-founding geography.
- Include names because they appear in qualifying U.S. jurisdictional or approved founding-era records, not because citizenship is proven.
- Include Indigenous, slavery-era, post-emancipation, immigration, naturalization, and military sources only when name components are safely classifiable as first/given names or surnames/family names.
- Include all clearly identified given-name components, not only first-position given names.
- Include all clearly identified surname fields, including maiden, married, former, birth, Anglicized, and structured alternate surnames.
- Preserve diacritics, transliterations, punctuation, and historical variants as distinct spellings.
- Include recognized historical given-name abbreviations such as Wm, Thos, Geo, and Chas. Exclude single-letter initials from the public first-name set.

## Privacy posture

The project must never publish or retain in public outputs:

- full-name pairs
- profile URLs
- record IDs
- person IDs
- locations
- dates
- addresses
- employers
- occupations
- military units
- household relationships
- inferred relationships or inferred surnames

## Quality posture

Trusted structured fields may be accepted automatically. OCR-derived, handwritten, unstructured, culturally ambiguous, or weakly parsed names require review before public release.

## v0.1 implementation

The first execution package focuses on high-structure sources:

- 2020 Census first names
- 2020 Census last names
- 2010 Census surnames
- SSA national baby names
- Optional SSA state and territory baby names
