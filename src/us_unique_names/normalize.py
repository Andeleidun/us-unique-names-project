from __future__ import annotations

import re
import unicodedata
import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

NORMALIZATION_VERSION = "2026-07-01"

# Conservative list. Additions should be review-controlled.
APPROVED_TERMINAL_PERIOD_ABBREVIATIONS = {
    "Alexr", "Benj", "Cath", "Chas", "Eliz", "Geo", "Jas", "Jno",
    "Jos", "Margt", "Nathl", "Richd", "Robt", "Saml", "Thos", "Wm",
}
DEFAULT_ALLOWLIST = Path(__file__).resolve().parents[2] / "config" / "historical_abbreviations_allowlist.csv"

_WHITESPACE_RE = re.compile(r"\s+")
@dataclass(frozen=True)
class NormalizedName:
    display: str
    name_key: str
    sort_key: str
    ascii_search_key: str


def trim_and_collapse(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    return _WHITESPACE_RE.sub(" ", value.strip())


@lru_cache(maxsize=8)
def load_terminal_period_abbreviations(path: str | Path | None = None) -> frozenset[str]:
    """Load approved historical abbreviations that may drop a terminal period."""
    abbreviations = set(APPROVED_TERMINAL_PERIOD_ABBREVIATIONS)
    allowlist_path = Path(path) if path else DEFAULT_ALLOWLIST
    if not allowlist_path.exists():
        return frozenset(abbreviations)
    with allowlist_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            abbreviation = trim_and_collapse(row.get("abbreviation", ""))
            if abbreviation:
                abbreviations.add(abbreviation)
    return frozenset(abbreviations)


def normalize_display(value: str) -> str:
    display = trim_and_collapse(value)
    if display.endswith("."):
        without_period = display[:-1]
        if without_period in load_terminal_period_abbreviations():
            display = without_period
    return display


def make_name_key(display: str) -> str:
    # Deliberately conservative: case-fold and normalize only.
    # Do not strip punctuation, hyphens, apostrophes, spaces, or diacritics.
    return unicodedata.normalize("NFC", display).casefold()


def make_sort_key(display: str) -> str:
    # Stable, human-friendly-ish sort key. Identity is never based on this.
    nfd = unicodedata.normalize("NFD", display).casefold()
    without_marks = "".join(ch for ch in nfd if not unicodedata.combining(ch))
    return _WHITESPACE_RE.sub(" ", without_marks).strip()


def make_ascii_search_key(display: str) -> str:
    nfd = unicodedata.normalize("NFD", display).casefold()
    no_marks = "".join(ch for ch in nfd if not unicodedata.combining(ch))
    return no_marks.encode("ascii", "ignore").decode("ascii")


def normalize_name(value: str) -> Optional[NormalizedName]:
    if value is None:
        return None
    display = normalize_display(str(value))
    if not display:
        return None
    return NormalizedName(
        display=display,
        name_key=make_name_key(display),
        sort_key=make_sort_key(display),
        ascii_search_key=make_ascii_search_key(display),
    )
