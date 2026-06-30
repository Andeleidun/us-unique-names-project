from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .census import extract_census_1990_txt, extract_census_excel, extract_census_surname_zip
from .ssa import extract_ssa_national_path, extract_ssa_state_or_territory_zip


def _single_allowed_output(source: dict[str, Any]) -> str:
    """Return the single name type configured for parsers that need it."""
    outputs = source.get("allowed_outputs") or []
    if len(outputs) != 1 or outputs[0] not in {"first", "last"}:
        raise ValueError(f"{source.get('source_id')}: parser requires exactly one allowed output")
    return str(outputs[0])


def extract_registered_source(source: dict[str, Any], path: str | Path) -> Iterator[tuple[str, str, str]]:
    """Dispatch a registered source to its configured extractor."""
    parser = source.get("parser")
    if parser == "ssa_national_zip":
        yield from extract_ssa_national_path(path)
    elif parser in {"ssa_state_zip", "ssa_territory_zip"}:
        yield from extract_ssa_state_or_territory_zip(path)
    elif parser == "census_xlsx_name_column":
        yield from extract_census_excel(path, _single_allowed_output(source))
    elif parser in {"census_2010_surnames_zip", "census_2000_surnames_zip"}:
        yield from extract_census_surname_zip(path, _single_allowed_output(source))
    elif parser == "census_1990_txt":
        yield from extract_census_1990_txt(path, _single_allowed_output(source))
    else:
        raise ValueError(f"{source.get('source_id')}: unsupported parser {parser!r}")
