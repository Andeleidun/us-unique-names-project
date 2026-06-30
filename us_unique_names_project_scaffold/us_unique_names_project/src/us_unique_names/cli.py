from __future__ import annotations

import argparse
from pathlib import Path

from .db import complete_source_run, ingest_names, init_db, load_sources, start_source_run
from .export_release import export_release, validate_release_dir
from .extractors import (
    extract_census_1990_txt,
    extract_census_excel,
    extract_census_surname_zip,
    extract_ssa_national_zip,
    extract_ssa_state_or_territory_zip,
)

DEFAULT_SOURCES = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"
DEFAULT_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "names.sql"

SOURCE_CATEGORIES = {
    "ssa_national_baby_names": "ssa_aggregate",
    "ssa_state_baby_names": "ssa_aggregate",
    "ssa_territory_baby_names": "ssa_aggregate",
    "census_2020_first_names_by_sex": "census_aggregate",
    "census_2020_last_names_race_hispanic": "census_aggregate",
    "census_2010_surnames": "census_aggregate",
    "census_2000_surnames": "census_aggregate",
    "census_1990_last_names": "census_aggregate",
    "census_1990_female_first_names": "census_aggregate",
    "census_1990_male_first_names": "census_aggregate",
}


def _source_category(source_id: str) -> str:
    return SOURCE_CATEGORIES.get(source_id, "unknown")


def _ensure_db(db: str) -> None:
    init_db(db, DEFAULT_SCHEMA)
    load_sources(db, DEFAULT_SOURCES)


def cmd_init_db(args: argparse.Namespace) -> None:
    _ensure_db(args.db)
    print(f"initialized {args.db}")


def _ingest(args: argparse.Namespace, rows) -> None:
    _ensure_db(args.db)
    run_id = start_source_run(args.db, args.source_id, args.path)
    stats = ingest_names(args.db, run_id, args.source_id, _source_category(args.source_id), rows)
    complete_source_run(args.db, run_id)
    print(stats)


def cmd_ingest_ssa_national(args: argparse.Namespace) -> None:
    _ingest(args, extract_ssa_national_zip(args.path))


def cmd_ingest_ssa_state(args: argparse.Namespace) -> None:
    _ingest(args, extract_ssa_state_or_territory_zip(args.path))


def cmd_ingest_census_zip(args: argparse.Namespace) -> None:
    _ingest(args, extract_census_surname_zip(args.path, args.name_type))


def cmd_ingest_census_excel(args: argparse.Namespace) -> None:
    _ingest(args, extract_census_excel(args.path, args.name_type))


def cmd_ingest_census_1990(args: argparse.Namespace) -> None:
    _ingest(args, extract_census_1990_txt(args.path, args.name_type))


def cmd_export(args: argparse.Namespace) -> None:
    manifest = export_release(args.db, args.release_dir, DEFAULT_SOURCES)
    print(f"exported {args.release_dir} with {len(manifest['artifacts'])} artifacts")


def cmd_validate_release(args: argparse.Namespace) -> None:
    ok, errors, warnings = validate_release_dir(args.release_dir)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if not ok:
        raise SystemExit(1)
    print("release validation passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="U.S. unique names ingestion and release tooling")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("init-db")
    p.add_argument("db")
    p.set_defaults(func=cmd_init_db)

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
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
