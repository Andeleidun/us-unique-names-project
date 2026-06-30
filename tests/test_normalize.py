from pathlib import Path

from us_unique_names.normalize import load_terminal_period_abbreviations, normalize_name


def test_preserves_distinct_diacritics_and_transliterations():
    jose = normalize_name("José")
    jose_plain = normalize_name("Jose")
    assert jose is not None and jose_plain is not None
    assert jose.name_key != jose_plain.name_key
    assert jose.display == "José"


def test_preserves_hyphen_and_space_distinctions():
    hyphen = normalize_name("Anne-Marie")
    space = normalize_name("Anne Marie")
    assert hyphen is not None and space is not None
    assert hyphen.name_key != space.name_key


def test_casefolds_for_deduplication_only():
    a = normalize_name("John")
    b = normalize_name("john")
    assert a is not None and b is not None
    assert a.name_key == b.name_key
    assert a.display == "John"


def test_approved_terminal_period_abbreviation_normalizes_display():
    wm = normalize_name(" Wm. ")
    assert wm is not None
    assert wm.display == "Wm"


def test_abbreviation_allowlist_can_be_loaded_from_config(tmp_path: Path):
    allowlist = tmp_path / "allowlist.csv"
    allowlist.write_text("abbreviation,common_expansion,notes\nAbc,Example,\n", encoding="utf-8")
    load_terminal_period_abbreviations.cache_clear()
    try:
        assert "Abc" in load_terminal_period_abbreviations(allowlist)
    finally:
        load_terminal_period_abbreviations.cache_clear()


def test_unapproved_period_is_preserved():
    value = normalize_name("A.J.")
    assert value is not None
    assert value.display == "A.J."
