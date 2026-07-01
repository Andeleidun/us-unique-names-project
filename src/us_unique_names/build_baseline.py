from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .db import complete_source_run, ingest_names, init_db, load_sources, start_source_run
from .db import sha256_path
from .download_sources import download_registered_sources
from .export_release import export_release, validate_release_dir
from .extractors import extract_registered_source
from .registry import iter_sources
from .release_coverage import generate_source_status
from .source_checks import validate_expected_source_counts

DEFAULT_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "names.sql"


def _clean_release_dir(release_dir: Path) -> None:
    """Remove generated release artifacts before rebuilding a release directory."""
    release_dir.mkdir(parents=True, exist_ok=True)
    for path in release_dir.iterdir():
        if path.is_file():
            path.unlink()


def _write_release_notes(
    release_dir: Path,
    included: list[str],
    failures: list[dict[str, str]],
    source_paths: dict[str, str | Path],
    release_version: str | None = None,
) -> None:
    """Write human-readable release notes for an automated baseline build."""
    title = f"{release_version} Release notes" if release_version else "Release notes"
    lines = [
        f"# {title}",
        "",
        "U.S. Unique First and Last Name Sets - aggregate baseline.",
        "",
        "This is a precision-first baseline built from selected aggregate Census and SSA sources. It is not exhaustive U.S. name coverage.",
        "",
        "Included sources:",
        "",
    ]
    lines.extend(f"- `{source_id}`" for source_id in included)
    if failures:
        lines.extend(["", "Failed or skipped enabled sources:", ""])
        lines.extend(f"- `{item['source_id']}`: {item['stage']} failed: {item['error']}" for item in failures)
    if source_paths:
        lines.extend(["", "Local source overrides:", ""])
        lines.extend(
            f"- `{source_id}`: supplied from `{Path(path).as_posix()}`"
            for source_id, path in sorted(source_paths.items())
        )
    lines.extend([
        "",
        "Scope and data-quality notes:",
        "",
        "- Public canonical CSV files contain only one `name` column.",
        "- Public name displays are title-cased for release usability; source-observed casing is retained in the DuckDB reproducibility bundle.",
        "- Source coverage is thresholded by the original Census and SSA publication rules.",
        "- Names can appear in both first-name and last-name files; this overlap is expected.",
        "- OCR, person-level records, historical unstructured records, and disabled optional sources are not included in this baseline.",
        "",
        "License and source terms:",
        "",
        "- The dataset compilation, processing code, documentation, and release metadata are licensed under Creative Commons Attribution 4.0 International (`CC-BY-4.0`).",
        "- Underlying source data may be public domain or governed by their source terms.",
        "- Upstream source citations and source identifiers are listed in `SOURCE_CITATIONS.md`.",
        "",
        "Metadata contains only safe source-level fields.",
    ])
    (release_dir / "release_notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_baseline(
    sources_path: str | Path,
    raw_dir: str | Path,
    db_path: str | Path,
    release_dir: str | Path,
    force_download: bool = False,
    overwrite_db: bool = False,
    skip_count_checks: bool = False,
    source_paths: dict[str, str | Path] | None = None,
    release_version: str | None = None,
) -> dict[str, Any]:
    """Download, ingest enabled sources, export, validate, and report a baseline release."""
    sources_path = Path(sources_path)
    raw_dir = Path(raw_dir)
    db_path = Path(db_path)
    release_dir = Path(release_dir)
    failures: list[dict[str, str]] = []
    included: list[str] = []
    count_checks: list[dict[str, Any]] = []
    source_paths = source_paths or {}

    download_rows = download_registered_sources(
        sources_path,
        raw_dir,
        force=force_download,
        continue_on_error=True,
        skip_source_ids=set(source_paths),
    )
    failures.extend(
        {"source_id": row["source_id"], "stage": "download", "error": row["error"]}
        for row in download_rows
        if row.get("status") == "failed"
    )

    if db_path.exists():
        if not overwrite_db:
            raise FileExistsError(f"{db_path} already exists; pass --overwrite-db to replace it")
        db_path.unlink()
    init_db(db_path, DEFAULT_SCHEMA)
    load_sources(db_path, sources_path)

    for source in iter_sources(sources_path, include_disabled=False):
        source_id = str(source["source_id"])
        source_file = Path(source_paths[source_id]) if source_id in source_paths else raw_dir / str(source["file_name"])
        if not source_file.exists():
            if not any(item["source_id"] == source_id for item in failures):
                failures.append({"source_id": source_id, "stage": "download", "error": "raw file is missing"})
            continue
        try:
            if not skip_count_checks:
                check = validate_expected_source_counts(source, source_file)
                count_checks.append(check)
                if not check["ok"]:
                    raise ValueError("; ".join(check["errors"]))
            run_id = start_source_run(db_path, source_id, source_file)
            stats = ingest_names(
                db_path,
                run_id,
                source_id,
                str(source["source_category"]),
                extract_registered_source(source, source_file),
            )
            complete_source_run(db_path, run_id)
            included.append(source_id)
            print(f"{source_id}: {stats}")
        except Exception as exc:  # noqa: BLE001
            failures.append({"source_id": source_id, "stage": "ingest", "error": str(exc)})

    _clean_release_dir(release_dir)
    _write_release_notes(release_dir, included, failures, source_paths, release_version)
    build_notes = {
        "included": included,
        "failures": failures,
        "download_rows": download_rows,
        "source_overrides": {
            source_id: {"path": str(path), "sha256": sha256_path(Path(path))}
            for source_id, path in source_paths.items()
            if Path(path).exists()
        },
        "count_checks": count_checks,
    }
    (release_dir / "build_notes.json").write_text(json.dumps(build_notes, indent=2), encoding="utf-8")
    coverage = generate_source_status(sources_path, raw_dir, db_path, release_dir)
    (release_dir / "release_coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")
    manifest = export_release(db_path, release_dir, sources_path)
    ok, errors, warnings = validate_release_dir(release_dir)
    build_notes["manifest_artifact_count"] = len(manifest["artifacts"])
    build_notes["validation"] = {"ok": ok, "errors": errors, "warnings": warnings}
    (release_dir / "build_notes.json").write_text(json.dumps(build_notes, indent=2), encoding="utf-8")
    coverage = generate_source_status(sources_path, raw_dir, db_path, release_dir)
    (release_dir / "release_coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")
    manifest = export_release(db_path, release_dir, sources_path)
    ok, errors, warnings = validate_release_dir(release_dir)
    build_notes["manifest_artifact_count"] = len(manifest["artifacts"])
    build_notes["validation"] = {"ok": ok, "errors": errors, "warnings": warnings}
    (release_dir / "build_notes.json").write_text(json.dumps(build_notes, indent=2), encoding="utf-8")
    export_release(db_path, release_dir, sources_path)
    ok, errors, warnings = validate_release_dir(release_dir)
    if not ok:
        raise RuntimeError(f"release validation failed: {errors}")
    build_notes["validation"] = {"ok": ok, "errors": errors, "warnings": warnings}
    return build_notes
