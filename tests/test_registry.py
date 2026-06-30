from pathlib import Path

from us_unique_names.registry import iter_sources, source_by_id


REQUIRED_ENABLED_FIELDS = {
    "source_id",
    "source_category",
    "download_url",
    "file_name",
    "parser",
    "allowed_outputs",
    "retention",
}


def test_registry_loads_download_parser_and_enabled_fields():
    source = source_by_id(Path("config/sources.yaml"), "ssa_national_baby_names")
    assert source["enabled"] is True
    assert source["parser"] == "ssa_national_zip"
    assert source["file_name"] == "ssa_names_national.zip"
    assert source["download_url"].endswith("/names.zip")


def test_default_enabled_sources_exclude_optional_expansion_sources():
    enabled = {source["source_id"] for source in iter_sources(Path("config/sources.yaml"), include_disabled=False)}
    assert enabled == {
        "census_2020_first_names_by_sex",
        "census_2020_last_names_race_hispanic",
        "census_2010_surnames",
        "ssa_national_baby_names",
    }
    assert "nppes_npi_v2_individual_providers" not in enabled


def test_enabled_sources_have_required_registry_fields():
    for source in iter_sources(Path("config/sources.yaml"), include_disabled=False):
        missing = [field for field in REQUIRED_ENABLED_FIELDS if field not in source]
        assert missing == [], f"{source.get('source_id')} missing {missing}"
        assert source["allowed_outputs"]
        assert "persist_person_rows" in source["retention"]
        assert "stream_only_fields" in source["retention"]
