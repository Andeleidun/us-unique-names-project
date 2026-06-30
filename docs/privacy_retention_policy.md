# Privacy and Retention Policy

## Public-output boundary

Public files may contain only deduplicated name strings and safe source-level metadata:

- `first_names.csv`: one column, `name`
- `last_names.csv`: one column, `name`
- metadata CSVs: `name`, `source_count`, `source_categories`, `confidence_tier`

Public files must not contain full names, locations, dates, source record IDs, URLs, occupations, employers, addresses, household relationships, military units, campaign committees, health care identifiers, or any other identifying context.

## Raw source handling

Aggregate sources may be retained under `data/raw/` when the source registry sets `raw_storage_allowed: true`.

Future person-level sources must default to:

```yaml
raw_storage_allowed: false
retention:
  retain_raw_file: false
  persist_person_rows: false
  stream_only_fields: [approved_name_fields_only]
```

For person-level sources, extractors must read the source stream, extract only approved first-name or last-name fields, write candidate names, and immediately discard all other data.

## Review-gated material

OCR, handwriting transcription, full-name-only fields, unstructured biographies, culturally ambiguous names, newspaper text, weak genealogy indexes, and uncertain historical abbreviations go to `review_queue` and cannot appear in public canonical files until accepted.

## Social platform policy

Facebook, LinkedIn, and similar platforms must not be scraped. They may be considered only if a source provides explicit written authorization, a compliant public dataset, and a retention policy compatible with this project.
