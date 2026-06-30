#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from us_unique_names.download_sources import download_registered_sources


def main() -> None:
    """Run source downloads from the command line."""
    parser = argparse.ArgumentParser(description="Download enabled registered source files.")
    parser.add_argument("--sources", default="config/sources.yaml", help="Path to source registry YAML")
    parser.add_argument("--raw-dir", default="data/raw", help="Directory for raw downloaded files")
    parser.add_argument("--include-disabled", action="store_true", help="Download disabled optional sources too")
    parser.add_argument("--force", action="store_true", help="Re-download files that already exist")
    parser.add_argument("--continue-on-error", action="store_true", help="Record failed downloads and continue")
    args = parser.parse_args()

    rows = download_registered_sources(args.sources, args.raw_dir, args.include_disabled, args.force, args.continue_on_error)
    print(f"Wrote {Path(args.raw_dir) / 'raw_checksums.csv'} with {len(rows)} source(s)")


if __name__ == "__main__":
    main()
