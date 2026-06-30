from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path
from typing import Iterator

import pandas as pd

NAME_COLUMN_CANDIDATES = {
    "name", "surname", "last name", "last_name", "first name", "first_name",
    "firstname", "lastname", "names", "first", "last",
}


def _looks_like_name_column(col: object) -> bool:
    clean = re.sub(r"\s+", " ", str(col).strip().casefold())
    return clean in NAME_COLUMN_CANDIDATES or clean.endswith(" name")


def extract_census_excel(path: str | Path, name_type: str) -> Iterator[tuple[str, str, str]]:
    """Extract names from Census Excel files using flexible sheet/header detection.

    The extractor scans all sheets and accepts columns with obvious name-like headers.
    It yields only the name field and never yields counts or demographic columns.
    """
    workbook = pd.ExcelFile(path)
    for sheet in workbook.sheet_names:
        # Try a few header rows because public workbooks sometimes include title rows.
        for header in range(0, 6):
            try:
                df = pd.read_excel(workbook, sheet_name=sheet, header=header, dtype=str)
            except Exception:
                continue
            for col in df.columns:
                if _looks_like_name_column(col):
                    for value in df[col].dropna().astype(str):
                        if value.strip() and value.strip().casefold() not in {"name", "first name", "last name", "surname"}:
                            yield value, name_type, str(col)
                    return


def extract_census_surname_zip(zip_path: str | Path, name_type: str = "last") -> Iterator[tuple[str, str, str]]:
    """Extract surnames from Census 2000/2010 zip files.

    Expected files contain CSV or Excel data. Only the name/surname column is yielded.
    """
    with zipfile.ZipFile(zip_path) as zf:
        for member in sorted(zf.namelist()):
            lower = member.lower()
            if lower.endswith(".csv"):
                with zf.open(member) as fh:
                    text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
                    reader = csv.DictReader(text)
                    if not reader.fieldnames:
                        continue
                    candidate = None
                    for field in reader.fieldnames:
                        if _looks_like_name_column(field):
                            candidate = field
                            break
                    if not candidate:
                        # Common Census surname files use 'name'. If headers are missing, skip safely.
                        continue
                    for row in reader:
                        value = row.get(candidate)
                        if value:
                            yield value, name_type, candidate
            elif lower.endswith((".xlsx", ".xls")):
                # Extract to memory and let pandas inspect it.
                data = zf.read(member)
                tmp = io.BytesIO(data)
                yield from extract_census_excel(tmp, name_type)


def extract_census_1990_txt(path: str | Path, name_type: str) -> Iterator[tuple[str, str, str]]:
    """Extract the first whitespace-delimited token from 1990 Census name files."""
    with Path(path).open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            first_token = stripped.split()[0]
            yield first_token, name_type, "name"
