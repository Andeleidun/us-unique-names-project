from pathlib import Path

import yaml

from us_unique_names.download_sources import download_registered_sources


def test_downloader_uses_enabled_sources_and_writes_checksums(tmp_path: Path, monkeypatch):
    sources = tmp_path / "sources.yaml"
    sources.write_text(
        yaml.safe_dump({
            "sources": [
                {
                    "source_id": "enabled_source",
                    "enabled": True,
                    "download_url": "https://example.test/enabled.csv",
                    "file_name": "enabled.csv",
                },
                {
                    "source_id": "disabled_source",
                    "enabled": False,
                    "download_url": "https://example.test/disabled.csv",
                    "file_name": "disabled.csv",
                },
            ]
        }),
        encoding="utf-8",
    )

    def fake_download(url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f"from {url}\n", encoding="utf-8")

    monkeypatch.setattr("us_unique_names.download_sources.download", fake_download)
    rows = download_registered_sources(sources, tmp_path / "raw")

    assert [row["source_id"] for row in rows] == ["enabled_source"]
    assert (tmp_path / "raw" / "enabled.csv").exists()
    assert not (tmp_path / "raw" / "disabled.csv").exists()
    checksum_manifest = (tmp_path / "raw" / "raw_checksums.csv").read_text(encoding="utf-8")
    assert "source_id,file_name,sha256,status,error" in checksum_manifest
    assert "enabled_source,enabled.csv," in checksum_manifest
    assert "disabled_source" not in checksum_manifest


def test_downloader_skips_existing_files_unless_forced(tmp_path: Path, monkeypatch):
    sources = tmp_path / "sources.yaml"
    sources.write_text(
        yaml.safe_dump({
            "sources": [
                {
                    "source_id": "enabled_source",
                    "enabled": True,
                    "download_url": "https://example.test/enabled.csv",
                    "file_name": "enabled.csv",
                },
            ]
        }),
        encoding="utf-8",
    )
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "enabled.csv").write_text("existing\n", encoding="utf-8")
    calls = []

    def fake_download(url: str, dest: Path) -> None:
        calls.append(url)
        dest.write_text("fresh\n", encoding="utf-8")

    monkeypatch.setattr("us_unique_names.download_sources.download", fake_download)
    rows = download_registered_sources(sources, raw_dir)
    assert rows[0]["status"] == "skipped_existing"
    assert calls == []

    rows = download_registered_sources(sources, raw_dir, force=True)
    assert rows[0]["status"] == "downloaded"
    assert calls == ["https://example.test/enabled.csv"]
