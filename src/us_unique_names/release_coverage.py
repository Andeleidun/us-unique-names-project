from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from .db import sha256_path
from .download_sources import sha256_file
from .registry import iter_sources


def _source_runs_by_id(db_path: str | Path | None) -> dict[str, dict[str, Any]]:
    """Return completed source-run summaries keyed by source_id."""
    if not db_path or not Path(db_path).exists():
        return {}
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = con.execute(
            """
            SELECT source_id, COUNT(*) AS run_count, MAX(completed_at) AS completed_at
            FROM source_runs
            WHERE completed_at IS NOT NULL
            GROUP BY source_id
            """
        ).fetchall()
    finally:
        con.close()
    return {row[0]: {"run_count": row[1], "completed_at": row[2]} for row in rows}


def _load_build_notes(release_dir: str | Path | None) -> dict[str, Any]:
    """Load machine-readable build notes when present."""
    if not release_dir:
        return {}
    path = Path(release_dir) / "build_notes.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def generate_source_status(
    sources_path: str | Path,
    raw_dir: str | Path = "data/raw",
    db_path: str | Path | None = None,
    release_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize enabled, disabled, included, skipped, and failed sources."""
    runs = _source_runs_by_id(db_path)
    build_notes = _load_build_notes(release_dir)
    failures = {item["source_id"]: item for item in build_notes.get("failures", [])}
    overrides = build_notes.get("source_overrides", {})
    raw_path = Path(raw_dir)
    sources = []
    summary = {"included": 0, "failed": 0, "skipped": 0, "disabled": 0, "downloaded": 0}

    for source in iter_sources(sources_path, include_disabled=True):
        source_id = str(source["source_id"])
        file_name = source.get("file_name")
        override_path = Path(overrides[source_id]["path"]) if source_id in overrides else None
        file_path = override_path if override_path else raw_path / str(file_name) if file_name else None
        raw_exists = bool(file_path and file_path.exists())
        raw_sha256 = sha256_path(file_path) if override_path and raw_exists else sha256_file(file_path) if file_path and raw_exists else None
        if not source.get("enabled", False):
            status = "disabled"
        elif source_id in runs:
            status = "included"
        elif source_id in failures:
            status = "failed"
        elif raw_exists:
            status = "downloaded"
        else:
            status = "skipped"
        summary[status] += 1
        sources.append({
            "source_id": source_id,
            "enabled": bool(source.get("enabled", False)),
            "status": status,
            "file_name": file_name,
            "source_path": str(file_path) if file_path else None,
            "source_path_override": str(override_path) if override_path else None,
            "raw_exists": raw_exists,
            "raw_sha256": raw_sha256,
            "run": runs.get(source_id),
            "failure": failures.get(source_id),
        })

    return {
        "summary": summary,
        "sources": sources,
        "release_dir": str(release_dir) if release_dir else None,
        "db_path": str(db_path) if db_path else None,
    }
