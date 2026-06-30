import csv
from pathlib import Path

from us_unique_names.db import complete_source_run, ingest_names, init_db, load_sources, start_source_run
from us_unique_names.export_release import export_release, validate_release_dir


def test_fixture_pipeline_exports_valid_release_without_source_downloads(tmp_path: Path):
    db = tmp_path / "names.duckdb"
    init_db(db, Path("schemas/names.sql"))
    load_sources(db, Path("config/sources.yaml"))

    rows_by_type: dict[str, list[tuple[str, str, str]]] = {"first": [], "last": []}
    with Path("examples/fixtures/fixture_names.csv").open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows_by_type[row["name_type"]].append((row["name"], row["name_type"], "name"))

    first_run_id = start_source_run(db, "ssa_national_baby_names")
    first_stats = ingest_names(
        db,
        first_run_id,
        "ssa_national_baby_names",
        "ssa_aggregate",
        rows_by_type["first"],
    )
    complete_source_run(db, first_run_id)

    last_run_id = start_source_run(db, "census_2010_surnames")
    last_stats = ingest_names(
        db,
        last_run_id,
        "census_2010_surnames",
        "census_aggregate",
        rows_by_type["last"],
    )
    complete_source_run(db, last_run_id)

    assert first_stats["accepted"] == 5
    assert last_stats["accepted"] == 4

    release_dir = tmp_path / "release"
    export_release(db, release_dir, Path("config/sources.yaml"))
    ok, errors, warnings = validate_release_dir(release_dir)
    assert ok, errors
    assert warnings == []
    assert (release_dir / "first_names.csv").read_text(encoding="utf-8").splitlines() == [
        "name",
        "John",
        "Jon",
        "Jose",
        "José",
        "Wm",
    ]
    assert (release_dir / "last_names.csv").read_text(encoding="utf-8").splitlines() == [
        "name",
        "De La Cruz",
        "O'Neil",
        "Smith",
        "Smyth",
    ]
