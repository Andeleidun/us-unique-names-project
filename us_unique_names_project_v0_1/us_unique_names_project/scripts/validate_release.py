#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd

PUBLIC_NAME_COLUMNS = ["name"]
BAD_PATTERNS = {
    "email_or_url": re.compile(r"(@|https?://|www\.)", re.IGNORECASE),
    "digit": re.compile(r"\d"),
    "comma": re.compile(r","),
}
BAD_TOKENS = {
    "mr", "mrs", "ms", "miss", "dr", "prof", "rev", "jr", "sr", "ii", "iii", "iv", "v",
    "phd", "md", "dds", "pvt", "sgt", "capt", "col", "gen", "llc", "inc", "co", "committee", "pac", "estate", "trust", "unknown", "infant"
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_public_csv(path: Path) -> list[str]:
    errors: list[str] = []
    df = pd.read_csv(path, dtype=str)
    if list(df.columns) != PUBLIC_NAME_COLUMNS:
        errors.append(f"{path.name}: expected columns {PUBLIC_NAME_COLUMNS}, got {list(df.columns)}")
        return errors
    names = df["name"].fillna("").astype(str)
    if names.str.strip().eq("").any():
        errors.append(f"{path.name}: contains empty or whitespace-only name")
    keys = names.str.casefold()
    if keys.duplicated().any():
        errors.append(f"{path.name}: contains duplicate casefolded names")
    sorted_names = list(names.sort_values(key=lambda s: s.str.casefold(), kind="mergesort"))
    if list(names) != sorted_names:
        errors.append(f"{path.name}: names are not sorted by casefolded sort key")
    for pattern_name, pattern in BAD_PATTERNS.items():
        bad = names[names.str.contains(pattern, na=False)]
        if len(bad):
            errors.append(f"{path.name}: found {pattern_name} pattern examples: {bad.head(5).tolist()}")
    token_bad = names[names.str.casefold().str.strip(". ").isin(BAD_TOKENS)]
    if len(token_bad):
        errors.append(f"{path.name}: found disallowed token examples: {token_bad.head(5).tolist()}")
    if path.name == "first_names.csv":
        initials = names[names.str.replace(".", "", regex=False).str.len().eq(1)]
        if len(initials):
            errors.append(f"{path.name}: found single-letter initials: {initials.head(10).tolist()}")
    return errors


def validate_checksums(release_dir: Path) -> list[str]:
    checksum_path = release_dir / "checksums.sha256"
    if not checksum_path.exists():
        return ["missing checksums.sha256"]
    errors = []
    for line in checksum_path.read_text().splitlines():
        if not line.strip():
            continue
        expected, file_name = line.split(None, 1)
        file_name = file_name.strip()
        actual_path = release_dir / file_name
        if not actual_path.exists():
            errors.append(f"checksum target missing: {file_name}")
            continue
        actual = sha256_file(actual_path)
        if actual != expected:
            errors.append(f"checksum mismatch for {file_name}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a generated release directory.")
    parser.add_argument("release_dir")
    args = parser.parse_args()
    release_dir = Path(args.release_dir)
    errors: list[str] = []
    for file_name in ["first_names.csv", "last_names.csv"]:
        path = release_dir / file_name
        if not path.exists():
            errors.append(f"missing required file: {file_name}")
        else:
            errors.extend(validate_public_csv(path))
    errors.extend(validate_checksums(release_dir))
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("Validation passed.")


if __name__ == "__main__":
    main()
