from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Iterator


def extract_ssa_national_zip(zip_path: str | Path) -> Iterator[tuple[str, str, str]]:
    """Yield (name, name_type, source_field) from SSA national yob*.txt files.

    SSA rows are: name, sex, count. Only the name is retained.
    """
    with zipfile.ZipFile(zip_path) as zf:
        for member in sorted(zf.namelist()):
            if not member.lower().endswith(".txt") or "/" in member:
                continue
            with zf.open(member) as fh:
                reader = csv.reader(io.TextIOWrapper(fh, encoding="utf-8"))
                for row in reader:
                    if not row:
                        continue
                    yield row[0], "first", "name"


def extract_ssa_state_or_territory_zip(zip_path: str | Path) -> Iterator[tuple[str, str, str]]:
    """Yield (name, name_type, source_field) from SSA state/territory files.

    State rows are usually: state, sex, year, name, count.
    Territory rows follow a similar layout. Only the name is retained.
    """
    with zipfile.ZipFile(zip_path) as zf:
        for member in sorted(zf.namelist()):
            if not member.lower().endswith(".txt") or "/" in member:
                continue
            with zf.open(member) as fh:
                reader = csv.reader(io.TextIOWrapper(fh, encoding="utf-8"))
                for row in reader:
                    if len(row) >= 5:
                        yield row[3], "first", "name"
