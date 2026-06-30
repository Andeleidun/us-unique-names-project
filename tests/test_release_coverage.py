from pathlib import Path

import yaml

from us_unique_names.release_coverage import generate_source_status


def test_source_status_summarizes_disabled_skipped_and_failed(tmp_path: Path):
    sources = tmp_path / "sources.yaml"
    sources.write_text(
        yaml.safe_dump({
            "sources": [
                {"source_id": "enabled_missing", "enabled": True, "file_name": "missing.csv"},
                {"source_id": "disabled_source", "enabled": False, "file_name": "disabled.csv"},
                {"source_id": "failed_source", "enabled": True, "file_name": "failed.csv"},
            ]
        }),
        encoding="utf-8",
    )
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    (release_dir / "build_notes.json").write_text(
        '{"failures":[{"source_id":"failed_source","stage":"download","error":"blocked"}]}',
        encoding="utf-8",
    )

    status = generate_source_status(sources, tmp_path / "raw", release_dir=release_dir)
    assert status["summary"]["skipped"] == 1
    assert status["summary"]["disabled"] == 1
    assert status["summary"]["failed"] == 1


def test_source_status_reports_source_path_overrides(tmp_path: Path):
    sources = tmp_path / "sources.yaml"
    override_dir = tmp_path / "names"
    override_dir.mkdir()
    (override_dir / "yob1880.txt").write_text("Mary,F,7065\n", encoding="utf-8")
    sources.write_text(
        yaml.safe_dump({
            "sources": [
                {"source_id": "ssa_national_baby_names", "enabled": True, "file_name": "ssa_names_national.zip"},
            ]
        }),
        encoding="utf-8",
    )
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    (release_dir / "build_notes.json").write_text(
        '{"source_overrides":{"ssa_national_baby_names":{"path":"' + str(override_dir).replace("\\", "\\\\") + '"}}}',
        encoding="utf-8",
    )

    status = generate_source_status(sources, tmp_path / "raw", release_dir=release_dir)
    source = status["sources"][0]
    assert source["raw_exists"]
    assert source["source_path_override"] == str(override_dir)
