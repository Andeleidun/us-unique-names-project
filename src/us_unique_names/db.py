from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import duckdb
import pandas as pd
import yaml

from .normalize import NORMALIZATION_VERSION, normalize_name
from .validate import VALIDATION_VERSION, validate_candidate_name

EXTRACTION_VERSION = "2026-07-01"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_path(path: Path) -> str:
    """Return a stable SHA-256 for a file or directory tree."""
    if path.is_file():
        return sha256_file(path)
    h = hashlib.sha256()
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        relative = child.relative_to(path).as_posix()
        h.update(relative.encode("utf-8"))
        h.update(b"\0")
        with child.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    return h.hexdigest()


def connect(db_path: str | Path):
    return duckdb.connect(str(db_path))


def _insert_rows(con, view_name: str, columns: list[str], rows: list[list[object]], sql: str) -> None:
    """Insert rows through a temporary DataFrame view for efficient bulk writes."""
    if not rows:
        return
    df = pd.DataFrame(rows, columns=columns)
    con.register(view_name, df)
    try:
        con.execute(sql)
    finally:
        con.unregister(view_name)


def init_db(db_path: str | Path, schema_path: str | Path | None = None) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = Path(schema_path) if schema_path else Path(__file__).resolve().parents[2] / "schemas" / "names.sql"
    sql = schema_path.read_text(encoding="utf-8")
    con = connect(db_path)
    try:
        con.execute(sql)
    finally:
        con.close()


def load_sources(db_path: str | Path, sources_yaml: str | Path) -> int:
    con = connect(db_path)
    count = 0
    data = yaml.safe_load(Path(sources_yaml).read_text(encoding="utf-8"))
    try:
        for source in data.get("sources", []):
            con.execute(
                """
                INSERT OR REPLACE INTO sources
                (source_id, name, source_category, source_url, download_url, license, access_method,
                 raw_storage_allowed, structured_fields_available, review_required, display_authority,
                 enabled, parser, file_name, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    source["source_id"], source["name"], source["source_category"],
                    source.get("source_url"), source.get("download_url"), source.get("license"),
                    source.get("access_method", "download"), bool(source.get("raw_storage_allowed", False)),
                    bool(source.get("structured_fields_available", False)), bool(source.get("review_required", True)),
                    bool(source.get("display_authority", False)), bool(source.get("enabled", False)),
                    source.get("parser"), source.get("file_name"), source.get("notes"),
                ],
            )
            count += 1
    finally:
        con.close()
    return count


def start_source_run(db_path: str | Path, source_id: str, source_file: str | Path | None = None, notes: str | None = None) -> str:
    run_id = str(uuid.uuid4())
    checksum = sha256_path(Path(source_file)) if source_file else None
    now = utc_now()
    con = connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO source_runs
            (run_id, source_id, downloaded_at, source_file_checksum, extractor_version,
             normalization_version, validation_version, started_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [run_id, source_id, now, checksum, EXTRACTION_VERSION, NORMALIZATION_VERSION, VALIDATION_VERSION, now, notes],
        )
    finally:
        con.close()
    return run_id


def complete_source_run(db_path: str | Path, run_id: str) -> None:
    con = connect(db_path)
    try:
        con.execute("UPDATE source_runs SET completed_at = ? WHERE run_id = ?", [utc_now(), run_id])
    finally:
        con.close()


def ingest_names(
    db_path: str | Path,
    run_id: str,
    source_id: str,
    source_category: str,
    rows: Iterable[tuple[str, str, str]],
    default_confidence: str = "high",
) -> dict[str, int]:
    """Ingest rows of (raw_name, name_type, source_field)."""
    con = connect(db_path)
    stats = {"accepted": 0, "review": 0, "rejected": 0, "pending": 0, "seen": 0}
    now = utc_now()
    candidate_rows = []
    review_rows = []
    name_rows = []
    assertion_rows = []
    allow_single_token_disallowed = source_category in {"census_aggregate", "ssa_aggregate"}
    try:
        for raw_name, name_type, source_field in rows:
            stats["seen"] += 1
            normalized = normalize_name(raw_name)
            if normalized is None:
                decision = "rejected"
                rejection_reason = "empty after normalization"
                candidate_name = str(raw_name) if raw_name is not None else ""
            else:
                validation = validate_candidate_name(
                    normalized.display,
                    name_type,
                    allow_single_token_disallowed=allow_single_token_disallowed,
                )
                candidate_name = normalized.display
                if validation.errors:
                    decision = "rejected"
                    rejection_reason = "; ".join(validation.errors)
                elif validation.warnings:
                    decision = "review"
                    rejection_reason = "; ".join(validation.warnings)
                elif name_type == "unknown":
                    decision = "review"
                    rejection_reason = "unknown name type"
                else:
                    decision = "accepted"
                    rejection_reason = None

            candidate_id = str(uuid.uuid4())
            candidate_rows.append(
                [candidate_id, run_id, source_id, candidate_name, name_type, source_field, default_confidence, decision, rejection_reason, now]
            )
            stats[decision] += 1

            if decision == "review":
                review_rows.append(
                    [str(uuid.uuid4()), candidate_name, name_type, source_id, rejection_reason or "review", "needs_expert_review", now],
                )

            if decision != "accepted" or normalized is None:
                continue

            name_rows.append(
                [name_type, normalized.display, normalized.name_key, normalized.sort_key, normalized.ascii_search_key, "high", now, now],
            )
            assertion_rows.append(
                [name_type, normalized.name_key, source_id, source_category, EXTRACTION_VERSION, now, "high"],
            )

        con.execute("BEGIN TRANSACTION")
        _insert_rows(
            con,
            "candidate_rows",
            [
                "candidate_id",
                "run_id",
                "source_id",
                "candidate_name",
                "candidate_name_type",
                "source_field",
                "extraction_confidence",
                "decision",
                "rejection_reason",
                "created_at",
            ],
            candidate_rows,
            """
            INSERT INTO candidate_names
            (candidate_id, run_id, source_id, candidate_name, candidate_name_type, source_field,
             extraction_confidence, decision, rejection_reason, created_at)
            SELECT candidate_id, run_id, source_id, candidate_name, candidate_name_type, source_field,
                   extraction_confidence, decision, rejection_reason, created_at
            FROM candidate_rows
            """,
        )
        _insert_rows(
            con,
            "review_rows",
            ["review_id", "candidate_name", "candidate_name_type", "source_id", "reason", "proposed_decision", "created_at"],
            review_rows,
            """
            INSERT INTO review_queue
            (review_id, candidate_name, candidate_name_type, source_id, reason, proposed_decision, created_at)
            SELECT review_id, candidate_name, candidate_name_type, source_id, reason, proposed_decision, created_at
            FROM review_rows
            """,
        )
        _insert_rows(
            con,
            "name_rows",
            [
                "name_type",
                "name_display",
                "name_key",
                "sort_key",
                "ascii_search_key",
                "confidence_tier",
                "created_at",
                "updated_at",
            ],
            name_rows,
            """
            INSERT INTO names
            (name_type, name_display, name_key, sort_key, ascii_search_key, confidence_tier, created_at, updated_at)
            SELECT name_type, name_display, name_key, sort_key, ascii_search_key, confidence_tier, created_at, updated_at
            FROM name_rows
            ON CONFLICT (name_type, name_key) DO UPDATE SET
              updated_at = EXCLUDED.updated_at,
              confidence_tier = CASE
                WHEN names.confidence_tier = 'high' THEN names.confidence_tier
                ELSE EXCLUDED.confidence_tier
              END
            """,
        )
        _insert_rows(
            con,
            "assertion_rows",
            [
                "name_type",
                "name_key",
                "source_id",
                "source_category",
                "extraction_version",
                "observed_at",
                "confidence_tier",
            ],
            assertion_rows,
            """
            INSERT OR IGNORE INTO source_assertions
            (name_type, name_key, source_id, source_category, extraction_version, observed_at, confidence_tier)
            SELECT name_type, name_key, source_id, source_category, extraction_version, observed_at, confidence_tier
            FROM assertion_rows
            """,
        )
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        con.close()
    return stats
