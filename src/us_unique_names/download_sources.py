from __future__ import annotations

import csv
import hashlib
import time
import urllib.request
from pathlib import Path

from .registry import iter_sources


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum for a local file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, retries: int = 3) -> None:
    """Download one URL to a destination path with simple retry handling."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "us-unique-names/0.1"})
            with urllib.request.urlopen(req, timeout=120) as response, dest.open("wb") as out:
                out.write(response.read())
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"failed to download {url}: {last_error}")


def download_registered_sources(
    sources_path: str | Path,
    raw_dir: str | Path,
    include_disabled: bool = False,
    force: bool = False,
    continue_on_error: bool = False,
    skip_source_ids: set[str] | None = None,
) -> list[dict[str, str]]:
    """Download registry entries and write a checksum manifest."""
    raw_path = Path(raw_dir)
    manifest_rows: list[dict[str, str]] = []
    skip_source_ids = skip_source_ids or set()
    for source in iter_sources(sources_path, include_disabled=include_disabled):
        download_url = source.get("download_url")
        file_name = source.get("file_name")
        if not download_url or not file_name:
            raise ValueError(f"{source.get('source_id')}: download_url and file_name are required")
        dest = raw_path / str(file_name)
        source_id = str(source["source_id"])
        if source_id in skip_source_ids:
            manifest_rows.append({
                "source_id": source_id,
                "file_name": dest.name,
                "sha256": "",
                "status": "skipped_override",
            })
            continue
        if dest.exists() and not force:
            print(f"Skipping {source_id}; {dest} already exists")
            manifest_rows.append({
                "source_id": source_id,
                "file_name": dest.name,
                "sha256": sha256_file(dest),
                "status": "skipped_existing",
            })
            continue
        print(f"Downloading {source_id} -> {dest}")
        try:
            download(str(download_url), dest)
            manifest_rows.append({
                "source_id": source_id,
                "file_name": dest.name,
                "sha256": sha256_file(dest),
                "status": "downloaded",
            })
        except Exception as exc:
            if not continue_on_error:
                raise
            manifest_rows.append({
                "source_id": source_id,
                "file_name": dest.name,
                "sha256": "",
                "status": "failed",
                "error": str(exc),
            })

    raw_path.mkdir(parents=True, exist_ok=True)
    with (raw_path / "raw_checksums.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_id", "file_name", "sha256", "status", "error"])
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow({
                "source_id": row["source_id"],
                "file_name": row["file_name"],
                "sha256": row["sha256"],
                "status": row.get("status", ""),
                "error": row.get("error", ""),
            })
    return manifest_rows
