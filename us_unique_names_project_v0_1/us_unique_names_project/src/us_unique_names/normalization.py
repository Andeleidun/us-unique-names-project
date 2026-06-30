from __future__ import annotations

import re
import unicodedata

# The public dataset should not include titles, suffixes, ranks, organizations, or initials.
TITLE_SUFFIX_RANK_OR_ORG = {
    "mr", "mrs", "ms", "miss", "dr", "prof", "rev", "sir", "madam",
    "jr", "sr", "ii", "iii", "iv", "v", "phd", "md", "dds", "esq",
    "pvt", "cpl", "sgt", "lt", "capt", "col", "gen", "adm",
    "llc", "inc", "co", "corp", "company", "committee", "pac", "estate", "trust",
    "unknown", "infant", "unnamed", "baby"
}

APPROVED_HISTORICAL_ABBREVIATIONS = {
    "wm", "thos", "geo", "chas", "jas", "jno", "margt", "eliz"
}

DIGIT_TRANSLITERATION_NOISE = re.compile(r"\d")
EMAIL_OR_URL = re.compile(r"(@|https?://|www\.)", re.IGNORECASE)
PHONE_LIKE = re.compile(r"\b\d{3}[-.) ]*\d{3}[-. ]*\d{4}\b")
DATE_LIKE = re.compile(r"\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b")
MULTI_SPACE = re.compile(r"\s+")


def normalize_display_name(value: object) -> str | None:
    """Normalize a source name while preserving meaningful spelling.

    Rules:
    - Unicode NFC
    - trim
    - collapse internal whitespace
    - strip terminal period from approved historical abbreviations
    - preserve diacritics, punctuation, hyphens, and apostrophes
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none", "null"}:
        return None
    s = unicodedata.normalize("NFC", s)
    s = MULTI_SPACE.sub(" ", s)
    if s.endswith(".") and s[:-1].casefold() in APPROVED_HISTORICAL_ABBREVIATIONS:
        s = s[:-1]
    return s or None


def name_key(name_display: str) -> str:
    return unicodedata.normalize("NFC", name_display).casefold()


def sort_key(name_display: str) -> str:
    return name_key(name_display)


def ascii_search_key(name_display: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name_display)
    ascii_only = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return ascii_only.casefold()


def is_single_letter_initial(name_display: str) -> bool:
    cleaned = name_display.strip().replace(".", "")
    return len(cleaned) == 1 and cleaned.isalpha()


def looks_invalid_public_name(name_display: str) -> str | None:
    """Return a rejection reason, or None if the token is acceptable for public release."""
    s = name_display.strip()
    folded = s.casefold().strip(". ")
    if not s:
        return "empty"
    if EMAIL_OR_URL.search(s):
        return "email_or_url"
    if PHONE_LIKE.search(s):
        return "phone_like"
    if DATE_LIKE.search(s):
        return "date_like"
    if DIGIT_TRANSLITERATION_NOISE.search(s):
        return "contains_digit"
    if is_single_letter_initial(s):
        return "single_letter_initial"
    if folded in TITLE_SUFFIX_RANK_OR_ORG:
        return "title_suffix_rank_org_or_placeholder"
    # Reject obvious full-name pairs in public exports. Compound last names such as "De La Cruz"
    # are valid when they come from a surname field, so this check is intentionally light.
    if "," in s:
        return "comma_separated_full_name_or_list"
    return None
