from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Iterable

import pandas as pd

NAME_COLUMN_CANDIDATES = [
    "name", "first name", "firstname", "first_name", "given name", "given_name",
    "surname", "last name", "lastname", "last_name", "family name", "family_name"
]


def _clean_col(col: object) -> str:
    return str(col).strip().casefold().replace("\n", " ").replace("_", " ")


def find_name_column(columns: Iterable[object], preferred: str | None = None) -> object:
    cleaned = {_clean_col(col): col for col in columns}
    if preferred:
        pref = _clean_col(preferred)
        if pref in cleaned:
            return cleaned[pref]
    for candidate in NAME_COLUMN_CANDIDATES:
        if candidate in cleaned:
            return cleaned[candidate]
    # Fallback: first column containing name/surname and not race/count/frequency/rank.
    for col in columns:
        c = _clean_col(col)
        if ("name" in c or "surname" in c) and not any(block in c for block in ["rank", "count", "frequency", "percent", "pct"]):
            return col
    raise ValueError(f"Unable to identify name column from columns: {list(columns)}")


def extract_census_xlsx_name_column(path: Path) -> set[str]:
    names: set[str] = set()
    # Census workbooks may include cover, note, or data sheets. Inspect all sheets.
    workbook = pd.ExcelFile(path)
    for sheet in workbook.sheet_names:
        try:
            df = workbook.parse(sheet_name=sheet, dtype=str)
        except Exception:
            continue
        if df.empty:
            continue
        try:
            col = find_name_column(df.columns)
        except ValueError:
            # Some Census files may have headers offset by a few rows.
            for header_row in range(1, 8):
                try:
                    df2 = workbook.parse(sheet_name=sheet, dtype=str, header=header_row)
                    col = find_name_column(df2.columns)
                    df = df2
                    break
                except Exception:
                    continue
            else:
                continue
        names.update(str(v) for v in df[col].dropna().tolist())
    return names


def extract_census_2010_surnames_zip(path: Path) -> set[str]:
    names: set[str] = set()
    with zipfile.ZipFile(path) as zf:
        csv_members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
        if not csv_members:
            raise ValueError(f"No CSV found in {path}")
        for member in csv_members:
            with zf.open(member) as fh:
                df = pd.read_csv(fh, dtype=str)
            col = find_name_column(df.columns)
            names.update(str(v) for v in df[col].dropna().tolist())
    return names


def extract_ssa_national_zip(path: Path) -> set[str]:
    names: set[str] = set()
    with zipfile.ZipFile(path) as zf:
        for member in zf.namelist():
            if not member.lower().endswith(".txt") or "/" in member:
                continue
            with zf.open(member) as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8", newline="")
                for line in text:
                    parts = line.strip().split(",")
                    if len(parts) >= 1 and parts[0]:
                        names.add(parts[0])
    return names


def extract_ssa_state_zip(path: Path) -> set[str]:
    names: set[str] = set()
    with zipfile.ZipFile(path) as zf:
        for member in zf.namelist():
            if not member.lower().endswith(".txt"):
                continue
            with zf.open(member) as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8", newline="")
                for line in text:
                    # Format: state,sex,year,name,count
                    parts = line.strip().split(",")
                    if len(parts) >= 4 and parts[3]:
                        names.add(parts[3])
    return names


def extract_ssa_territory_zip(path: Path) -> set[str]:
    # Territory file format generally follows the state file structure.
    return extract_ssa_state_zip(path)


PARSER_MAP = {
    "census_xlsx_name_column": extract_census_xlsx_name_column,
    "census_2010_surnames_zip": extract_census_2010_surnames_zip,
    "ssa_national_zip": extract_ssa_national_zip,
    "ssa_state_zip": extract_ssa_state_zip,
    "ssa_territory_zip": extract_ssa_territory_zip,
}
