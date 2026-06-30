from __future__ import annotations

import argparse
import json
from pathlib import Path

from .build_baseline import build_baseline
from .db import complete_source_run, ingest_names, init_db, load_sources, start_source_run
from .download_sources import download_registered_sources
from .export_release import export_release, validate_release_dir
from .extractors import (
    extract_registered_source,
    extract_census_1990_txt,
    extract_census_excel,
    extract_census_surname_zip,
    extract_ssa_national_zip,
    extract_ssa_state_or_territory_zip,
)
from .registry import source_by_id
from .release_coverage import generate_source_status
from .source_checks import validate_expected_source_counts

DEFAULT_SOURCES = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"
DEFAULT_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "names.sql"


def _source_category(source_id: str) -> str:
    """Return the configured source category for legacy ingest commands."""
    return str(source_by_id(DEFAULT_SOURCES, source_id).get("source_category", "unknown"))


def _ensure_db(db: str, sources: str | Path = DEFAULT_SOURCES) -> None:
    """Initialize the database and load the configured source registry."""
    init_db(db, DEFAULT_SCHEMA)
    load_sources(db, sources)


def cmd_init_db(args: argparse.Namespace) -> None:
    """Handle the init-db command."""
    _ensure_db(args.db)
    print(f"initialized {args.db}")


def cmd_download_sources(args: argparse.Namespace) -> None:
    """Handle the download-sources command."""
    rows = download_registered_sources(args.sources, args.raw_dir, args.include_disabled, args.force, args.continue_on_error)
    print(f"downloaded {len(rows)} source(s); wrote {Path(args.raw_dir) / 'raw_checksums.csv'}")


def _ingest(args: argparse.Namespace, rows) -> None:
    """Run common ingestion steps for legacy source-specific commands."""
    _ensure_db(args.db)
    run_id = start_source_run(args.db, args.source_id, args.path)
    stats = ingest_names(args.db, run_id, args.source_id, _source_category(args.source_id), rows)
    complete_source_run(args.db, run_id)
    print(stats)


def _registered_source_path(source: dict, raw_dir: str | Path, explicit_path: str | None) -> Path:
    """Resolve an ingest path from an explicit path or the source file_name."""
    if explicit_path:
        return Path(explicit_path)
    file_name = source.get("file_name")
    if not file_name:
        raise ValueError(f"{source.get('source_id')}: file_name is required when --path is omitted")
    return Path(raw_dir) / str(file_name)


def cmd_ingest_source(args: argparse.Namespace) -> None:
    """Handle registry-driven ingestion for one configured source."""
    source = source_by_id(args.sources, args.source_id)
    path = _registered_source_path(source, args.raw_dir, args.path)
    _ensure_db(args.db, args.sources)
    if not args.skip_count_check:
        check = validate_expected_source_counts(source, path)
        if not check["ok"]:
            raise SystemExit(f"{args.source_id}: expected-count check failed: {'; '.join(check['errors'])}")
    rows = extract_registered_source(source, path)
    run_id = start_source_run(args.db, args.source_id, path)
    stats = ingest_names(args.db, run_id, args.source_id, str(source["source_category"]), rows)
    complete_source_run(args.db, run_id)
    print(stats)


def cmd_source_status(args: argparse.Namespace) -> None:
    """Handle source coverage/status reporting."""
    status = generate_source_status(args.sources, args.raw_dir, args.db, args.release_dir)
    if args.json:
        print(json.dumps(status, indent=2))
        return
    print("status,count")
    for key, value in status["summary"].items():
        print(f"{key},{value}")
    print("")
    print("source_id,status,enabled,raw_exists")
    for source in status["sources"]:
        print(f"{source['source_id']},{source['status']},{source['enabled']},{source['raw_exists']}")


def cmd_build_baseline(args: argparse.Namespace) -> None:
    """Handle automated baseline build orchestration."""
    source_paths = {}
    for value in args.source_path:
        if "=" not in value:
            raise SystemExit("--source-path must use source_id=path")
        source_id, path = value.split("=", 1)
        source_paths[source_id] = path
    notes = build_baseline(
        args.sources,
        args.raw_dir,
        args.db,
        args.release_dir,
        force_download=args.force_download,
        overwrite_db=args.overwrite_db,
        skip_count_checks=args.skip_count_checks,
        source_paths=source_paths,
        release_version=args.release_version,
    )
    print(json.dumps(notes, indent=2))


def cmd_ingest_ssa_national(args: argparse.Namespace) -> None:
    """Handle legacy SSA national ingestion."""
    _ingest(args, extract_ssa_national_zip(args.path))


def cmd_ingest_ssa_state(args: argparse.Namespace) -> None:
    """Handle legacy SSA state or territory ingestion."""
    _ingest(args, extract_ssa_state_or_territory_zip(args.path))


def cmd_ingest_census_zip(args: argparse.Namespace) -> None:
    """Handle legacy Census ZIP ingestion."""
    _ingest(args, extract_census_surname_zip(args.path, args.name_type))


def cmd_ingest_census_excel(args: argparse.Namespace) -> None:
    """Handle legacy Census Excel ingestion."""
    _ingest(args, extract_census_excel(args.path, args.name_type))


def cmd_ingest_census_1990(args: argparse.Namespace) -> None:
    """Handle legacy Census 1990 text ingestion."""
    _ingest(args, extract_census_1990_txt(args.path, args.name_type))


def cmd_export(args: argparse.Namespace) -> None:
    """Handle release export."""
    manifest = export_release(args.db, args.release_dir, DEFAULT_SOURCES)
    print(f"exported {args.release_dir} with {len(manifest['artifacts'])} artifacts")


def cmd_validate_release(args: argparse.Namespace) -> None:
    """Handle release validation."""
    ok, errors, warnings = validate_release_dir(args.release_dir)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if not ok:
        raise SystemExit(1)
    print("release validation passed")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="U.S. unique names ingestion and release tooling")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("init-db")
    p.add_argument("db")
    p.set_defaults(func=cmd_init_db)

    p = sub.add_parser("download-sources")
    p.add_argument("--sources", default=str(DEFAULT_SOURCES))
    p.add_argument("--raw-dir", default="data/raw")
    p.add_argument("--include-disabled", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--continue-on-error", action="store_true")
    p.set_defaults(func=cmd_download_sources)

    p = sub.add_parser("ingest-source")
    p.add_argument("--db", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--path")
    p.add_argument("--raw-dir", default="data/raw")
    p.add_argument("--sources", default=str(DEFAULT_SOURCES))
    p.add_argument("--skip-count-check", action="store_true")
    p.set_defaults(func=cmd_ingest_source)

    p = sub.add_parser("source-status")
    p.add_argument("--sources", default=str(DEFAULT_SOURCES))
    p.add_argument("--raw-dir", default="data/raw")
    p.add_argument("--db")
    p.add_argument("--release-dir")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_source_status)

    p = sub.add_parser("build-baseline")
    p.add_argument("--sources", default=str(DEFAULT_SOURCES))
    p.add_argument("--raw-dir", default="data/raw")
    p.add_argument("--db", default="data/work/baseline.duckdb")
    p.add_argument("--release-dir", required=True)
    p.add_argument("--force-download", action="store_true")
    p.add_argument("--overwrite-db", action="store_true")
    p.add_argument("--skip-count-checks", action="store_true")
    p.add_argument("--source-path", action="append", default=[], help="Override one source path as source_id=path")
    p.add_argument("--release-version", help="Release label to include in generated release notes")
    p.set_defaults(func=cmd_build_baseline)

    p = sub.add_parser("ingest-ssa-national")
    p.add_argument("path")
    p.add_argument("--db", required=True)
    p.add_argument("--source-id", required=True)
    p.set_defaults(func=cmd_ingest_ssa_national)

    p = sub.add_parser("ingest-ssa-state")
    p.add_argument("path")
    p.add_argument("--db", required=True)
    p.add_argument("--source-id", required=True)
    p.set_defaults(func=cmd_ingest_ssa_state)

    p = sub.add_parser("ingest-census-zip")
    p.add_argument("path")
    p.add_argument("--db", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--name-type", choices=["first", "last"], required=True)
    p.set_defaults(func=cmd_ingest_census_zip)

    p = sub.add_parser("ingest-census-excel")
    p.add_argument("path")
    p.add_argument("--db", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--name-type", choices=["first", "last"], required=True)
    p.set_defaults(func=cmd_ingest_census_excel)

    p = sub.add_parser("ingest-census-1990")
    p.add_argument("path")
    p.add_argument("--db", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--name-type", choices=["first", "last"], required=True)
    p.set_defaults(func=cmd_ingest_census_1990)

    p = sub.add_parser("export")
    p.add_argument("--db", required=True)
    p.add_argument("--release-dir", required=True)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("validate-release")
    p.add_argument("release_dir")
    p.set_defaults(func=cmd_validate_release)

    return parser


def main() -> None:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
