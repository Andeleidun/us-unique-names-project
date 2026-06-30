from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_source_registry(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate the source registry."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise ValueError("source registry must contain a 'sources' list")
    return data


def iter_sources(path: str | Path, include_disabled: bool = True) -> list[dict[str, Any]]:
    """Return registered sources, optionally filtering disabled sources."""
    sources = load_source_registry(path)["sources"]
    if include_disabled:
        return sources
    return [source for source in sources if source.get("enabled", False)]


def source_by_id(path: str | Path, source_id: str) -> dict[str, Any]:
    """Return one source registry entry by source_id."""
    for source in iter_sources(path):
        if source.get("source_id") == source_id:
            return source
    raise KeyError(f"unknown source_id: {source_id}")
