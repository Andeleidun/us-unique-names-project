from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from .normalize import make_sort_key
from .validate import validate_public_rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_csv(path: Path, names: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name"])
        for name in names:
            writer.writerow([name])


def _query_names(con: duckdb.DuckDBPyConnection, name_type: str) -> list[str]:
    rows = con.execute(
        """
        SELECT name_display
        FROM names
        WHERE name_type = ? AND confidence_tier IN ('high', 'medium')
        ORDER BY sort_key, name_display
        """,
        [name_type],
    ).fetchall()
    return [row[0] for row in rows]


def _query_metadata(con: duckdb.DuckDBPyConnection, name_type: str) -> pd.DataFrame:
    return con.execute(
        """
        SELECT
          n.name_display AS name,
          COUNT(sa.source_id) AS source_count,
          string_agg(DISTINCT sa.source_category, ';' ORDER BY sa.source_category) AS source_categories,
          n.confidence_tier AS confidence_tier
        FROM names n
        JOIN source_assertions sa
          ON sa.name_type = n.name_type AND sa.name_key = n.name_key
        WHERE n.name_type = ? AND n.confidence_tier IN ('high', 'medium')
        GROUP BY n.name_display, n.sort_key, n.confidence_tier
        ORDER BY n.sort_key, n.name_display
        """,
        [name_type],
    ).fetchdf()


def _trusted_single_token_keys(release_dir: Path, name_type: str) -> set[str]:
    db_path = release_dir / "names.duckdb"
    if not db_path.exists():
        return set()
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = con.execute(
            """
            SELECT DISTINCT n.name_key
            FROM names n
            JOIN source_assertions sa
              ON sa.name_type = n.name_type AND sa.name_key = n.name_key
            WHERE n.name_type = ?
              AND sa.source_category IN ('census_aggregate', 'ssa_aggregate')
              AND regexp_matches(n.name_display, '^[^ ]+$')
            """,
            [name_type],
        ).fetchall()
    finally:
        con.close()
    return {row[0] for row in rows}


def export_release(db_path: str | Path, release_dir: str | Path, sources_yaml: str | Path | None = None) -> dict:
    db_path = Path(db_path)
    release_dir = Path(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))
    try:
        first_names = _query_names(con, "first")
        last_names = _query_names(con, "last")
        _write_csv(release_dir / "first_names.csv", first_names)
        _write_csv(release_dir / "last_names.csv", last_names)

        pd.DataFrame({"name": first_names}).to_parquet(release_dir / "first_names.parquet", index=False)
        pd.DataFrame({"name": last_names}).to_parquet(release_dir / "last_names.parquet", index=False)
        _query_metadata(con, "first").to_csv(release_dir / "first_name_metadata.csv", index=False)
        _query_metadata(con, "last").to_csv(release_dir / "last_name_metadata.csv", index=False)
    finally:
        con.close()

    shutil.copy2(db_path, release_dir / "names.duckdb")
    if sources_yaml:
        shutil.copy2(sources_yaml, release_dir / "sources.yaml")

    release_notes = release_dir / "release_notes.md"
    if not release_notes.exists():
        release_notes.write_text(
            "# Release notes\n\n"
            "Baseline release generated from accepted source assertions. "
            "Public files contain only deduplicated names.\n",
            encoding="utf-8",
        )

    artifacts = []
    for path in sorted(release_dir.iterdir()):
        if path.is_file() and path.name not in {"manifest.json", "checksums.sha256"}:
            artifacts.append({
                "filename": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })

    manifest = {
        "release_created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "privacy_policy": "public CSV and Parquet files contain only one name column; metadata contains safe source-level fields only",
        "artifacts": artifacts,
    }
    (release_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    with (release_dir / "checksums.sha256").open("w", encoding="utf-8") as f:
        for artifact in artifacts:
            f.write(f"{artifact['sha256']}  {artifact['filename']}\n")

    return manifest


def validate_release_dir(release_dir: str | Path) -> tuple[bool, list[str], list[str]]:
    release_dir = Path(release_dir)
    errors: list[str] = []
    warnings: list[str] = []

    for filename, name_type in [("first_names.csv", "first"), ("last_names.csv", "last")]:
        path = release_dir / filename
        if not path.exists():
            errors.append(f"missing {filename}")
            continue
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != ["name"]:
                errors.append(f"{filename}: expected exactly one column named 'name'")
                continue
            names = [row["name"] for row in reader]
        result = validate_public_rows(names, name_type, _trusted_single_token_keys(release_dir, name_type))
        errors.extend([f"{filename}: {e}" for e in result.errors])
        warnings.extend([f"{filename}: {w}" for w in result.warnings])
        if names != sorted(names, key=lambda x: (make_sort_key(x), x)):
            warnings.append(f"{filename}: display order differs from normalized release sort order")

    checksum_path = release_dir / "checksums.sha256"
    if checksum_path.exists():
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            expected, filename = line.split(maxsplit=1)
            filename = filename.strip()
            actual_path = release_dir / filename
            if not actual_path.exists():
                errors.append(f"checksum references missing file {filename}")
                continue
            actual = sha256_file(actual_path)
            if actual != expected:
                errors.append(f"checksum mismatch for {filename}")
    else:
        errors.append("missing checksums.sha256")

    return not errors, errors, warnings
