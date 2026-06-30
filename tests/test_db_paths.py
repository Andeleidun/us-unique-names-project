from pathlib import Path

from us_unique_names.db import sha256_path


def test_sha256_path_hashes_directory_contents_stably(tmp_path: Path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("b", encoding="utf-8")
    first = sha256_path(tmp_path)
    second = sha256_path(tmp_path)
    assert first == second
    assert len(first) == 64
