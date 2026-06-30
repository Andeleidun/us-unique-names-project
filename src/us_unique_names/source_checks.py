from __future__ import annotations

from pathlib import Path
from typing import Any

from .extractors import extract_registered_source


def validate_expected_source_counts(source: dict[str, Any], path: str | Path) -> dict[str, Any]:
    """Validate extracted row counts against registry expectations."""
    expected = source.get("expected_rows") or {}
    row_count = sum(1 for _ in extract_registered_source(source, path))
    errors: list[str] = []
    minimum = expected.get("min")
    maximum = expected.get("max")
    if minimum is not None and row_count < int(minimum):
        errors.append(f"row count {row_count} is below expected minimum {minimum}")
    if maximum is not None and row_count > int(maximum):
        errors.append(f"row count {row_count} is above expected maximum {maximum}")
    return {
        "source_id": source.get("source_id"),
        "file_name": source.get("file_name"),
        "row_count": row_count,
        "expected": expected,
        "ok": not errors,
        "errors": errors,
    }
