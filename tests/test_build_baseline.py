import json
from pathlib import Path

import yaml

from us_unique_names.build_baseline import build_baseline


def test_build_baseline_cleans_stale_release_files_and_records_final_manifest_count(tmp_path: Path):
    sources = tmp_path / "sources.yaml"
    source_dir = tmp_path / "names"
    source_dir.mkdir()
    (source_dir / "yob1880.txt").write_text("Mary,F,7065\nJr,M,5\n", encoding="utf-8")
    sources.write_text(
        yaml.safe_dump({
            "sources": [
                {
                    "source_id": "ssa_national_baby_names",
                    "name": "SSA National Baby Names",
                    "source_category": "ssa_aggregate",
                    "source_url": "https://www.ssa.gov/oact/babynames/limits.html",
                    "download_url": "https://www.ssa.gov/oact/babynames/names.zip",
                    "file_name": "ssa_names_national.zip",
                    "parser": "ssa_national_zip",
                    "enabled": True,
                    "license": "public_domain_or_us_gov",
                    "access_method": "download",
                    "raw_storage_allowed": True,
                    "structured_fields_available": True,
                    "review_required": False,
                    "display_authority": False,
                    "allowed_outputs": ["first"],
                    "retention": {"retain_raw_file": True, "persist_person_rows": False, "stream_only_fields": ["name"]},
                    "expected_rows": {"min": 2, "max": 2},
                }
            ]
        }),
        encoding="utf-8",
    )
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    (release_dir / "stale.txt").write_text("stale", encoding="utf-8")

    build_baseline(
        sources,
        tmp_path / "raw",
        tmp_path / "names.duckdb",
        release_dir,
        overwrite_db=True,
        source_paths={"ssa_national_baby_names": source_dir},
        release_version="v0.1.0",
    )

    assert not (release_dir / "stale.txt").exists()
    build_notes = json.loads((release_dir / "build_notes.json").read_text(encoding="utf-8"))
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    release_notes = (release_dir / "release_notes.md").read_text(encoding="utf-8")
    assert build_notes["manifest_artifact_count"] == len(manifest["artifacts"])
    assert build_notes["validation"]["ok"]
    assert "# v0.1.0 Release notes" in release_notes
    assert "precision-first baseline" in release_notes
    assert "not exhaustive U.S. name coverage" in release_notes
    assert "`ssa_national_baby_names`: supplied from" in release_notes
    assert "CC-BY-4.0" in release_notes
    assert "Underlying source data may be public domain or governed by their source terms" in release_notes
