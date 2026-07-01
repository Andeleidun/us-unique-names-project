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
        [("MARY", "first", "name"), ("SMITH", "last", "name"), ("DE LA CRUZ", "last", "name"), ("J.", "first", "name")],
    )
    complete_source_run(db, run_id)
    assert stats["accepted"] == 3
    assert stats["rejected"] == 1

    release_dir = tmp_path / "release"
    export_release(db, release_dir, Path("config/sources.yaml"))
    ok, errors, warnings = validate_release_dir(release_dir)
    assert ok, errors
    assert warnings == []
    assert (release_dir / "first_names.csv").read_text(encoding="utf-8").splitlines() == ["name", "Mary"]
    assert (release_dir / "last_names.csv").read_text(encoding="utf-8").splitlines() == ["name", "De La Cruz", "Smith"]
    assert (release_dir / "first_names.parquet").exists()
    assert (release_dir / "last_names.parquet").exists()
    assert (release_dir / "first_name_metadata.csv").exists()
    assert (release_dir / "last_name_metadata.csv").exists()
    assert (release_dir / "manifest.json").exists()
    assert (release_dir / "checksums.sha256").exists()
    assert (release_dir / "sources.yaml").exists()
    assert (release_dir / "LICENSE").exists()


def test_title_case_release_name_handles_word_separators():
    from us_unique_names.export_release import title_case_release_name

    assert title_case_release_name("O'NEIL") == "O'Neil"
    assert title_case_release_name("ANNE-MARIE") == "Anne-Marie"
    assert title_case_release_name("DE LA CRUZ") == "De La Cruz"


def test_release_validation_accepts_normalized_sort_key_order(tmp_path: Path):
    db = tmp_path / "names.duckdb"
    init_db(db, Path("schemas/names.sql"))
    load_sources(db, Path("config/sources.yaml"))
    run_id = start_source_run(db, "ssa_national_baby_names")
    ingest_names(
        db,
        run_id,
        "ssa_national_baby_names",
        "ssa_aggregate",
        [("Zane", "first", "name"), ("Émile", "first", "name")],
    )
    complete_source_run(db, run_id)

    release_dir = tmp_path / "release"
    export_release(db, release_dir, Path("config/sources.yaml"))
    ok, errors, warnings = validate_release_dir(release_dir)
    assert ok, errors
    assert warnings == []
    assert (release_dir / "first_names.csv").read_text(encoding="utf-8").splitlines() == ["name", "Émile", "Zane"]


def test_release_validation_uses_metadata_without_duckdb_for_trusted_single_tokens(tmp_path: Path):
    db = tmp_path / "names.duckdb"
    init_db(db, Path("schemas/names.sql"))
    load_sources(db, Path("config/sources.yaml"))
    run_id = start_source_run(db, "ssa_national_baby_names")
    ingest_names(db, run_id, "ssa_national_baby_names", "ssa_aggregate", [("JR", "first", "name")])
    complete_source_run(db, run_id)

    release_dir = tmp_path / "release"
    export_release(db, release_dir, Path("config/sources.yaml"), include_duckdb=False)
    ok, errors, warnings = validate_release_dir(release_dir)
    assert ok, errors
    assert warnings == []
