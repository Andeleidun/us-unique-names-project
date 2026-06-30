# AGENTS.md

These instructions apply to the entire repository.

## Project Purpose

This repository builds privacy-preserving U.S. first-name and last-name datasets. The canonical public outputs are:

- `first_names.csv`
- `last_names.csv`

Each public canonical file must contain exactly one column named `name`.

## Privacy Boundary

Never publish full names, source record IDs, locations, dates, employers, occupations, URLs, addresses, demographic context, relationship data, military units, or person-level source rows. Metadata may contain only safe source-level fields such as source counts, source categories, and confidence tiers.

## Source Policy

Register every source in `config/sources.yaml` before ingestion. Default work should use structured aggregate Census and SSA sources. Person-level, OCR, historical, NPPES, FEC, Wikidata, ORCID, or unstructured sources require review or explicit approval before ingestion.

## Normalization Policy

Normalize to NFC, trim and collapse whitespace, and casefold only for identity keys. Preserve diacritics, punctuation, hyphens, apostrophes, and spaces. Do not use phonetic matching or transliteration collapse for canonical identity.

## Review Policy

Ambiguous, culturally uncertain, unstructured, OCR-derived, full-name-only, weakly parsed, or source-context-dependent records go to review. Review, rejected, and pending candidates must not enter public canonical files.

## Engineering Rules

Keep schema, config, docs, and tests aligned. Add focused tests for normalization, validation, extractors, source registry changes, downloader behavior, and release export. Preserve correctness and prefer direct implementation that fits the small package structure.

## Local Process

Use PowerShell and `rg` for local work. Use Python package commands such as `python -m pytest` and `python -m us_unique_names.cli ...`. Do not download live source files or add network-dependent behavior unless the user explicitly asks for it.
