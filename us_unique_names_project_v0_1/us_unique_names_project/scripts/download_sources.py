#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import time
import urllib.request
from pathlib import Path

import yaml


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, retries: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "us-unique-names-research/0.1"})
            with urllib.request.urlopen(req, timeout=120) as response, dest.open("wb") as out:
                out.write(response.read())
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to download {url}: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download approved source files.")
    parser.add_argument("--sources", required=True, help="Path to source registry YAML")
    parser.add_argument("--raw-dir", required=True, help="Directory for raw downloaded files")
    parser.add_argument("--include-disabled", action="store_true", help="Download disabled optional sources too")
    args = parser.parse_args()

    sources_path = Path(args.sources)
    raw_dir = Path(args.raw_dir)
    registry = yaml.safe_load(sources_path.read_text())
    manifest_rows = []

    for source in registry["sources"]:
        if not source.get("enabled", False) and not args.include_disabled:
            continue
        dest = raw_dir / source["file_name"]
        print(f"Downloading {source['source_id']} -> {dest}")
        download(source["url"], dest)
        manifest_rows.append(f"{source['source_id']},{dest.name},{sha256_file(dest)}")

    (raw_dir / "raw_checksums.csv").write_text("source_id,file_name,sha256\n" + "\n".join(manifest_rows) + "\n")
    print(f"Wrote {raw_dir / 'raw_checksums.csv'}")


if __name__ == "__main__":
    main()
