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
  source_id TEXT NOT NULL,
  source_category TEXT NOT NULL,
  extraction_version TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  confidence_tier TEXT NOT NULL,
  PRIMARY KEY (name_type, name_key, source_id)
);

CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  source_category TEXT NOT NULL,
  source_url TEXT,
  license TEXT,
  access_method TEXT NOT NULL,
  raw_storage_allowed INTEGER NOT NULL DEFAULT 0,
  structured_fields_available INTEGER NOT NULL DEFAULT 0,
  review_required INTEGER NOT NULL DEFAULT 0,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS review_queue (
  review_id TEXT PRIMARY KEY,
  candidate_name TEXT NOT NULL,
  candidate_name_type TEXT CHECK (candidate_name_type IN ('first', 'last', 'unknown')),
  source_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  proposed_decision TEXT CHECK (proposed_decision IN ('accept', 'reject', 'needs_expert_review')),
  reviewer_notes TEXT,
  created_at TEXT NOT NULL,
  reviewed_at TEXT
);
