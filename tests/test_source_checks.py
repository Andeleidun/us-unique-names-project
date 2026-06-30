import zipfile
from pathlib import Path

from us_unique_names.source_checks import validate_expected_source_counts


def test_expected_source_count_check_passes_for_matching_extract_count(tmp_path: Path):
    path = tmp_path / "names.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("yob1880.txt", "Mary,F,7065\nJohn,M,9655\n")
    source = {
        "source_id": "ssa_national_baby_names",
        "file_name": "names.zip",
        "parser": "ssa_national_zip",
        "expected_rows": {"min": 2, "max": 2},
    }
    result = validate_expected_source_counts(source, path)
    assert result["ok"]
    assert result["row_count"] == 2


def test_expected_source_count_check_reports_out_of_range(tmp_path: Path):
    path = tmp_path / "names.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("yob1880.txt", "Mary,F,7065\n")
    source = {
        "source_id": "ssa_national_baby_names",
        "file_name": "names.zip",
        "parser": "ssa_national_zip",
        "expected_rows": {"min": 2},
    }
    result = validate_expected_source_counts(source, path)
    assert not result["ok"]
    assert "below expected minimum" in result["errors"][0]


def test_expected_source_count_check_accepts_extracted_ssa_directory(tmp_path: Path):
    (tmp_path / "yob1880.txt").write_text("Mary,F,7065\nJohn,M,9655\n", encoding="utf-8")
    source = {
        "source_id": "ssa_national_baby_names",
        "file_name": "names",
        "parser": "ssa_national_zip",
        "expected_rows": {"min": 2, "max": 2},
    }
    result = validate_expected_source_counts(source, tmp_path)
    assert result["ok"]
    assert result["row_count"] == 2
