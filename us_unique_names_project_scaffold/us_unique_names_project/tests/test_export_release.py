from pathlib import Path

from us_unique_names.db import init_db, load_sources, start_source_run, ingest_names, complete_source_run
from us_unique_names.export_release import export_release, validate_release_dir


def test_export_release_roundtrip(tmp_path: Path):
    db = tmp_path / "names.duckdb"
    init_db(db, Path("schemas/names.sql"))
    load_sources(db, Path("config/sources.yaml"))
    run_id = start_source_run(db, "ssa_national_baby_names")
    stats = ingest_names(
        db,
        run_id,
        "ssa_national_baby_names",
        "ssa_aggregate",
        [("Mary", "first", "name"), ("Smith", "last", "name"), ("J.", "first", "name")],
    )
    complete_source_run(db, run_id)
    assert stats["accepted"] == 2
    assert stats["rejected"] == 1

    release_dir = tmp_path / "release"
    export_release(db, release_dir, Path("config/sources.yaml"))
    ok, errors, warnings = validate_release_dir(release_dir)
    assert ok, errors
    assert (release_dir / "first_names.csv").read_text(encoding="utf-8").splitlines() == ["name", "Mary"]
    assert (release_dir / "last_names.csv").read_text(encoding="utf-8").splitlines() == ["name", "Smith"]
