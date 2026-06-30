from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

NORMALIZATION_VERSION = "2026-07-01"

# Conservative list. Additions should be review-controlled.
APPROVED_TERMINAL_PERIOD_ABBREVIATIONS = {
    "Alexr", "Benj", "Cath", "Chas", "Eliz", "Geo", "Jas", "Jno",
    "Jos", "Margt", "Nathl", "Richd", "Robt", "Saml", "Thos", "Wm",
}

_WHITESPACE_RE = re.compile(r"\s+")
_COMBINING_MARK_RE = re.compile(r"[\u0300-\u036f]")


@dataclass(frozen=True)
class NormalizedName:
    display: str
    name_key: str
    sort_key: str
    ascii_search_key: str


def trim_and_collapse(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    return _WHITESPACE_RE.sub(" ", value.strip())


def normalize_display(value: str) -> str:
    display = trim_and_collapse(value)
    if display.endswith("."):
        without_period = display[:-1]
        if without_period in APPROVED_TERMINAL_PERIOD_ABBREVIATIONS:
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
