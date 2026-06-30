import zipfile
from pathlib import Path

from us_unique_names.extractors.ssa import extract_ssa_national_zip, extract_ssa_state_or_territory_zip
from us_unique_names.extractors.census import extract_census_1990_txt, extract_census_surname_zip


def test_extract_ssa_national_zip(tmp_path: Path):
    path = tmp_path / "names.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("yob1880.txt", "Mary,F,7065\nJohn,M,9655\n")
    assert list(extract_ssa_national_zip(path)) == [("Mary", "first", "name"), ("John", "first", "name")]


def test_extract_ssa_state_zip(tmp_path: Path):
    path = tmp_path / "state.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("AK.TXT", "AK,F,1910,Mary,14\n")
    assert list(extract_ssa_state_or_territory_zip(path)) == [("Mary", "first", "name")]


def test_extract_census_surname_zip(tmp_path: Path):
    path = tmp_path / "names.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("Names_2010Census.csv", "name,rank,count\nSmith,1,2442977\n")
    assert list(extract_census_surname_zip(path)) == [("Smith", "last", "name")]


def test_extract_census_1990_txt(tmp_path: Path):
    path = tmp_path / "dist.all.last"
    path.write_text("MOORE 0.312 5.312 9\n", encoding="utf-8")
    assert list(extract_census_1990_txt(path, "last")) == [("MOORE", "last", "name")]
