# Zenodo Release Guide

Use this guide to publish the v0.1.0 dataset artifacts to Zenodo.

Assigned DOI: `10.5281/zenodo.21100479`

## Recommended Path

Publish a direct Zenodo upload for v0.1.0. This works without GitHub release automation and lets the two curated ZIP artifacts be the canonical deposit files.

Upload these files:

- `data/releases/us-unique-names-v0.1.0-public.zip`
- `data/releases/us-unique-names-v0.1.0-reproducibility.zip`

Use the metadata in `.zenodo.json` for the Zenodo form.
Use `SOURCE_CITATIONS.md` for source citation review and identifiers.

## Zenodo Form Values

- Resource type: Dataset
- Title: U.S. Unique First and Last Name Sets v0.1.0: Aggregate Baseline
- Publication date: 2026-07-01
- Version: 0.1.0
- DOI: 10.5281/zenodo.21100479
- Creators: U.S. Unique First and Last Name Sets contributors
- License: Creative Commons Attribution 4.0 International
- Access right: Open access
- Related identifier: https://github.com/Andeleidun/us-unique-names-project
- Relation: Is supplement to

Add the upstream source URLs in `.zenodo.json` as related identifiers with relation `Is derived from`.

Description:

```text
Precision-first aggregate baseline of unique U.S. first-name and last-name spellings derived from selected Census and SSA aggregate sources. Public canonical files contain one title-cased name column. This release is not exhaustive U.S. name coverage; source coverage is thresholded by original Census and SSA publication rules.

The public artifact excludes raw source data and the working DuckDB database. The reproducibility artifact includes the DuckDB database, build notes, release coverage, source registry copy, checksums, and metadata needed to inspect the generated release.

SSA national baby-name data was supplied via a local extracted copy of the official SSA national names ZIP because the SSA endpoint blocked automated download in this environment.

The dataset compilation, processing code, documentation, and release metadata are licensed under CC BY 4.0. Underlying source data may be public domain or governed by their source terms.
```

Source citations are provided in `SOURCE_CITATIONS.md`. The source landing pages and direct source file URLs are also included in `.zenodo.json` as related identifiers.

## Manual Publish Steps

1. Log in to Zenodo.
2. Create a new upload.
3. Upload the public and reproducibility ZIP artifacts listed above.
4. Fill the metadata using `.zenodo.json` and the form values in this guide.
5. Verify the DOI is `10.5281/zenodo.21100479`.
6. Preview the draft record and verify both ZIP files, version, license, and description.
7. Publish the record.
8. After publishing, verify the public DOI resolves at `https://doi.org/10.5281/zenodo.21100479`.

## GitHub Integration Option

Zenodo can also archive a public GitHub repository and issue a new DOI whenever a new GitHub release is created. Use that path only after the GitHub release object for `v0.1.0` exists and contains both ZIP artifacts.

GitHub integration checklist:

1. Confirm the GitHub repository is public.
2. Confirm `LICENSE`, `CITATION.cff`, and `.zenodo.json` are committed on the default branch.
3. Log in to Zenodo with GitHub.
4. Enable the repository on Zenodo's GitHub integration page.
5. Create or edit the GitHub release `v0.1.0` and attach both ZIP artifacts.
6. Verify that Zenodo archived the release and assigned a DOI.

## Validation Before Publishing

Run:

```bash
python -m us_unique_names.cli validate-release data/releases/2026-06-30-baseline-public
python -m us_unique_names.cli validate-release data/releases/2026-06-30-baseline-full
```

Expected artifact sizes from the local build:

- `us-unique-names-v0.1.0-public.zip`: approximately 3.3 MB
- `us-unique-names-v0.1.0-reproducibility.zip`: approximately 216 MB
