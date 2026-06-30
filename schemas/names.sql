CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  source_category TEXT NOT NULL,
  source_url TEXT,
  download_url TEXT,
  license TEXT,
  access_method TEXT NOT NULL,
  raw_storage_allowed BOOLEAN NOT NULL DEFAULT false,
  structured_fields_available BOOLEAN NOT NULL DEFAULT false,
  review_required BOOLEAN NOT NULL DEFAULT true,
  display_authority BOOLEAN NOT NULL DEFAULT false,
  enabled BOOLEAN NOT NULL DEFAULT false,
  parser TEXT,
  file_name TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS source_runs (
  run_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  source_release_date TEXT,
  downloaded_at TEXT,
  source_file_checksum TEXT,
  extractor_version TEXT NOT NULL,
  normalization_version TEXT NOT NULL,
  validation_version TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS candidate_names (
  candidate_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES source_runs(run_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  candidate_name TEXT NOT NULL,
  candidate_name_type TEXT NOT NULL CHECK (candidate_name_type IN ('first', 'last', 'unknown')),
  source_field TEXT,
  extraction_confidence TEXT NOT NULL CHECK (extraction_confidence IN ('high', 'medium', 'low', 'review')),
  decision TEXT NOT NULL CHECK (decision IN ('accepted', 'review', 'rejected', 'pending')),
  rejection_reason TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS names (
  name_type TEXT NOT NULL CHECK (name_type IN ('first', 'last')),
  name_display TEXT NOT NULL,
  name_key TEXT NOT NULL,
  sort_key TEXT NOT NULL,
  ascii_search_key TEXT,
  confidence_tier TEXT NOT NULL CHECK (confidence_tier IN ('high', 'medium', 'review', 'rejected')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (name_type, name_key)
);

CREATE TABLE IF NOT EXISTS source_assertions (
  name_type TEXT NOT NULL,
  name_key TEXT NOT NULL,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  source_category TEXT NOT NULL,
  extraction_version TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  confidence_tier TEXT NOT NULL CHECK (confidence_tier IN ('high', 'medium', 'review', 'rejected')),
  PRIMARY KEY (name_type, name_key, source_id)
);

CREATE TABLE IF NOT EXISTS review_queue (
  review_id TEXT PRIMARY KEY,
  candidate_name TEXT NOT NULL,
  candidate_name_type TEXT CHECK (candidate_name_type IN ('first', 'last', 'unknown')),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  reason TEXT NOT NULL,
  proposed_decision TEXT CHECK (proposed_decision IN ('accept', 'reject', 'needs_expert_review')),
  reviewer_notes TEXT,
  created_at TEXT NOT NULL,
  reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS validation_failures (
  failure_id TEXT PRIMARY KEY,
  release_date TEXT,
  artifact TEXT,
  severity TEXT NOT NULL CHECK (severity IN ('error', 'warning')),
  message TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS export_artifacts (
  artifact_id TEXT PRIMARY KEY,
  release_date TEXT NOT NULL,
  filename TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  row_count INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
