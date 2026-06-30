from us_unique_names.validate import validate_candidate_name, validate_public_rows


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


def test_allows_trusted_aggregate_single_token_first_names_that_match_title_tokens():
    assert validate_candidate_name("Jr", "first", allow_single_token_disallowed=True).valid
    assert validate_candidate_name("Trust", "first", allow_single_token_disallowed=True).valid


def test_public_rows_need_trusted_key_for_title_like_first_names():
    assert not validate_public_rows(["Jr"], "first").valid
    assert validate_public_rows(["Jr"], "first", trusted_single_token_keys={"jr"}).valid


def test_allows_single_token_surnames_that_match_org_or_rank_tokens():
    for value in ["CO", "DO", "COL", "CORP", "COMPANY"]:
        assert validate_candidate_name(value, "last").valid


def test_rejects_urls_emails_dates_and_digits():
    assert not validate_candidate_name("adair@example.com", "first").valid
    assert not validate_candidate_name("https://example.com/name", "last").valid
    assert not validate_candidate_name("John 2020", "first").valid
    assert not validate_candidate_name("2020-01-01", "last").valid


def test_rejects_aggregate_bucket_labels():
    assert not validate_candidate_name("ALL OTHER NAMES", "first", allow_single_token_disallowed=True).valid
    assert not validate_candidate_name("All Other Names", "last", allow_single_token_disallowed=True).valid


def test_allows_apostrophe_and_hyphen():
    assert validate_candidate_name("O'Neil", "last").valid
    assert validate_candidate_name("Anne-Marie", "first").valid
