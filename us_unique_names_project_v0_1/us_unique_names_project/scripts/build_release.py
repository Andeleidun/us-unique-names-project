#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from us_unique_names.extractors import PARSER_MAP  # noqa: E402
from us_unique_names.normalization import ascii_search_key, looks_invalid_public_name, name_key, normalize_display_name, sort_key  # noqa: E402

EXTRACTION_VERSION = "0.1.0"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_candidate(store: dict, metadata: dict, raw_value: object, name_type: str, source: dict) -> None:
    display = normalize_display_name(raw_value)
    if display is None:
        return
    rejection = looks_invalid_public_name(display)
    if rejection:
        return
    key = name_key(display)
    existing = store.setdefault(name_type, {})
    if key not in existing:
        existing[key] = {
            "name": display,
            "sort_key": sort_key(display),
            "ascii_search_key": ascii_search_key(display),
        }
    meta = metadata.setdefault((name_type, key), {
        "name": existing[key]["name"],
        "sources": set(),
        "categories": set(),
        "confidence_tier": "high" if source.get("structured_fields_available") else "medium",
    })
    meta["sources"].add(source["source_id"])
    meta["categories"].add(source["source_category"])


def dataframe_from_store(store: dict, name_type: str) -> pd.DataFrame:
    rows = list(store.get(name_type, {}).values())
    if not rows:
        return pd.DataFrame(columns=["name"])
    df = pd.DataFrame(rows)
    df = df.sort_values(["sort_key", "name"], kind="mergesort")
    return df[["name"]]


def metadata_dataframe(metadata: dict, name_type: str) -> pd.DataFrame:
    rows = []
    for (ntype, key), value in metadata.items():
        if ntype != name_type:
            continue
        rows.append({
            "name": value["name"],
            "source_count": len(value["sources"]),
            "source_categories": "|".join(sorted(value["categories"])),
            "confidence_tier": value["confidence_tier"],
        })
    if not rows:
        return pd.DataFrame(columns=["name", "source_count", "source_categories", "confidence_tier"])
    df = pd.DataFrame(rows)
    df["sort_key"] = df["name"].map(sort_key)
    df = df.sort_values(["sort_key", "name"], kind="mergesort").drop(columns=["sort_key"])
    return df


def write_duckdb(db_path: Path, first_df: pd.DataFrame, last_df: pd.DataFrame, first_meta: pd.DataFrame, last_meta: pd.DataFrame, sources: list[dict]) -> None:
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    schema = (ROOT / "sql" / "schema.sql").read_text()
    con.execute(schema)
    now = datetime.now(timezone.utc).isoformat()

    for name_type, df in [("first", first_df), ("last", last_df)]:
        for name in df["name"].tolist():
            con.execute(
                "INSERT INTO names VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [name_type, name, name_key(name), sort_key(name), ascii_search_key(name), "high", now, now],
            )

    for source in sources:
        con.execute(
            "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                source["source_id"], source["name"], source["source_category"], source.get("url"), source.get("license"),
                source.get("access_method", "download"), int(bool(source.get("raw_storage_allowed"))),
                int(bool(source.get("structured_fields_available"))), int(bool(source.get("review_required"))), source.get("notes"),
            ],
        )
    con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a public name-set release from downloaded approved sources.")
    parser.add_argument("--sources", required=True)
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--release-dir", required=True)
    parser.add_argument("--include-disabled", action="store_true")
    args = parser.parse_args()

    sources_path = Path(args.sources)
    raw_dir = Path(args.raw_dir)
    release_dir = Path(args.release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    registry = yaml.safe_load(sources_path.read_text())
    store: dict = {"first": {}, "last": {}}
    metadata: dict = {}
    used_sources: list[dict] = []

    for source in registry["sources"]:
        if not source.get("enabled", False) and not args.include_disabled:
            continue
        raw_path = raw_dir / source["file_name"]
        if not raw_path.exists():
            raise FileNotFoundError(f"Missing raw source {raw_path}. Run scripts/download_sources.py first.")
        parser_name = source["parser"]
        if parser_name not in PARSER_MAP:
            raise KeyError(f"Unknown parser: {parser_name}")
        print(f"Extracting {source['source_id']} from {raw_path}")
        raw_names = PARSER_MAP[parser_name](raw_path)
        for output_type in source["allowed_outputs"]:
            if output_type not in {"first", "last"}:
                continue
            for raw_name in raw_names:
                add_candidate(store, metadata, raw_name, output_type, source)
        used_sources.append(source)

    first_df = dataframe_from_store(store, "first")
    last_df = dataframe_from_store(store, "last")
    first_meta = metadata_dataframe(metadata, "first")
    last_meta = metadata_dataframe(metadata, "last")

    first_df.to_csv(release_dir / "first_names.csv", index=False)
    last_df.to_csv(release_dir / "last_names.csv", index=False)
    first_df.to_parquet(release_dir / "first_names.parquet", index=False)
    last_df.to_parquet(release_dir / "last_names.parquet", index=False)
    first_meta.to_csv(release_dir / "first_name_metadata.csv", index=False)
    last_meta.to_csv(release_dir / "last_name_metadata.csv", index=False)
    write_duckdb(release_dir / "names.duckdb", first_df, last_df, first_meta, last_meta, used_sources)
    shutil.copy2(sources_path, release_dir / "sources.yaml")

    manifest = {
        "release_created_at": datetime.now(timezone.utc).isoformat(),
        "extraction_version": EXTRACTION_VERSION,
        "counts": {
            "first_names": int(len(first_df)),
            "last_names": int(len(last_df)),
        },
        "sources": [s["source_id"] for s in used_sources],
        "public_schema": {"first_names.csv": ["name"], "last_names.csv": ["name"]},
        "privacy_note": "Canonical public files contain only deduplicated name strings.",
    }
    (release_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    checksum_lines = []
    for path in sorted(release_dir.iterdir()):
        if path.is_file() and path.name != "checksums.sha256":
            checksum_lines.append(f"{sha256_file(path)}  {path.name}")
    (release_dir / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
