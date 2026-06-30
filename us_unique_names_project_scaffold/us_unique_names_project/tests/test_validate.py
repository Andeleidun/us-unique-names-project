from us_unique_names.validate import validate_candidate_name


def test_rejects_single_letter_first_initial():
    result = validate_candidate_name("J.", "first")
    assert not result.valid
    assert any("single-letter" in e for e in result.errors)


def test_allows_compound_first_name():
    result = validate_candidate_name("Anne Marie", "first")
    assert result.valid


def test_rejects_title_suffix_or_rank_tokens():
    assert not validate_candidate_name("Dr", "first").valid
    assert not validate_candidate_name("Smith Jr", "last").valid
    assert not validate_candidate_name("Sgt", "first").valid


def test_rejects_urls_emails_dates_and_digits():
    assert not validate_candidate_name("adair@example.com", "first").valid
    assert not validate_candidate_name("https://example.com/name", "last").valid
    assert not validate_candidate_name("John 2020", "first").valid
    assert not validate_candidate_name("2020-01-01", "last").valid


def test_allows_apostrophe_and_hyphen():
    assert validate_candidate_name("O'Neil", "last").valid
    assert validate_candidate_name("Anne-Marie", "first").valid
