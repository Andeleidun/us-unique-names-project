from us_unique_names.normalization import normalize_display_name, looks_invalid_public_name, name_key


def test_preserves_diacritics():
    assert normalize_display_name(" José ") == "José"
    assert name_key("José") != name_key("Jose")


def test_historical_abbreviation_period_removed():
    assert normalize_display_name("Wm.") == "Wm"


def test_single_letter_initial_rejected():
    assert looks_invalid_public_name("J.") == "single_letter_initial"


def test_surname_punctuation_preserved():
    assert normalize_display_name("O'Neil") == "O'Neil"
