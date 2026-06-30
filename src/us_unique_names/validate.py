from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

VALIDATION_VERSION = "2026-07-01"

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.I)
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
DATE_RE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")
ANY_DIGIT_RE = re.compile(r"\d")
CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")
SINGLE_INITIAL_RE = re.compile(r"^[A-Za-z]\.?$")

DISALLOWED_EXACT_TOKENS = {
    "dr", "mr", "mrs", "ms", "miss", "mx", "prof", "rev", "hon",
    "jr", "sr", "ii", "iii", "iv", "v", "phd", "md", "dds", "do", "esq",
    "pvt", "sgt", "cpl", "lt", "capt", "maj", "col", "gen", "adm",
    "llc", "inc", "co", "corp", "company", "committee", "pac", "estate", "trust",
}

DISALLOWED_FIRST_NAME_TOKENS = DISALLOWED_EXACT_TOKENS
DISALLOWED_LAST_NAME_COMPONENT_TOKENS = DISALLOWED_EXACT_TOKENS
DISALLOWED_EXACT_NAMES = {
    "all other",
    "all other name",
    "all other names",
}

NAME_CHARS_RE = re.compile(r"^[\w\s\-'’.`´.]+$", re.UNICODE)


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


def _tokens(name: str) -> list[str]:
    return [t.strip(" .,'\"()[]{}") for t in re.split(r"\s+", name) if t.strip()]


def validate_candidate_name(name: str, name_type: str, allow_single_token_disallowed: bool = False) -> ValidationResult:
    """Validate one candidate public name."""
    result = ValidationResult(valid=True)
    if name_type not in {"first", "last", "unknown"}:
        result.add_error("invalid name_type")
        return result

    if name is None or not str(name).strip():
        result.add_error("empty or whitespace-only value")
        return result

    name = str(name).strip()
    normalized_exact = re.sub(r"\s+", " ", name.casefold())
    if normalized_exact in DISALLOWED_EXACT_NAMES:
        result.add_error("aggregate bucket label excluded from public names")

    if CONTROL_RE.search(name):
        result.add_error("control character present")
    if EMAIL_RE.search(name):
        result.add_error("email-like value")
    if URL_RE.search(name):
        result.add_error("url-like value")
    if PHONE_RE.search(name):
        result.add_error("phone-like value")
    if DATE_RE.search(name):
        result.add_error("date-like value")
    if ANY_DIGIT_RE.search(name):
        result.add_error("digit present")
    if not NAME_CHARS_RE.match(name):
        result.add_error("contains characters outside conservative name character set")

    tokens = _tokens(name)
    lowered_tokens = {t.casefold().rstrip(".") for t in tokens}
    disallowed_tokens = DISALLOWED_FIRST_NAME_TOKENS
    if allow_single_token_disallowed and len(lowered_tokens) == 1:
        disallowed_tokens = set()
    elif name_type == "last" and len(lowered_tokens) == 1:
        disallowed_tokens = set()
    elif name_type == "last":
        disallowed_tokens = DISALLOWED_LAST_NAME_COMPONENT_TOKENS
    forbidden = lowered_tokens.intersection(disallowed_tokens)
    if forbidden:
        result.add_error(f"disallowed title, suffix, rank, or organization token: {sorted(forbidden)[0]}")

    if name_type == "first" and SINGLE_INITIAL_RE.match(name):
        result.add_error("single-letter initial excluded from public first names")

    if "," in name:
        result.add_warning("comma present; review for full-name or inverted-name artifact")
    if "  " in name:
        result.add_warning("repeated whitespace present before normalization")

    return result


def validate_public_rows(
    rows: Iterable[str],
    name_type: str,
    trusted_single_token_keys: set[str] | None = None,
) -> ValidationResult:
    """Validate canonical public release rows."""
    result = ValidationResult(valid=True)
    seen: set[str] = set()
    trusted_single_token_keys = trusted_single_token_keys or set()
    from .normalize import normalize_name

    for row_number, name in enumerate(rows, start=2):
        normalized = normalize_name(name)
        if normalized is None:
            result.add_error(f"row {row_number}: empty name")
            continue
        if normalized.name_key in seen:
            result.add_error(f"row {row_number}: duplicate name key {normalized.name_key!r}")
        seen.add(normalized.name_key)
        row_result = validate_candidate_name(
            normalized.display,
            name_type,
            allow_single_token_disallowed=normalized.name_key in trusted_single_token_keys,
        )
        for err in row_result.errors:
            result.add_error(f"row {row_number}: {err}")
        for warning in row_result.warnings:
            result.add_warning(f"row {row_number}: {warning}")
    return result
