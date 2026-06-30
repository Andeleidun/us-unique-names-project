import subprocess
import sys
import zipfile
from pathlib import Path

import duckdb


def test_cli_ingest_source_uses_registry_parser(tmp_path: Path):
    source_zip = tmp_path / "ssa_names_national.zip"
    with zipfile.ZipFile(source_zip, "w") as zf:
        zf.writestr("yob1880.txt", "Mary,F,7065\nJohn,M,9655\n")

    db = tmp_path / "names.duckdb"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "us_unique_names.cli",
            "ingest-source",
            "--db",
            str(db),
            "--source-id",
            "ssa_national_baby_names",
            "--path",
            str(source_zip),
            "--skip-count-check",
        ],
        cwd=Path.cwd(),
        check=True,
        capture_output=True,
        text=True,
    )

    assert "'accepted': 2" in result.stdout
    con = duckdb.connect(str(db))
    try:
        names = con.execute("SELECT name_display FROM names ORDER BY name_display").fetchall()
    finally:
        con.close()
    assert names == [("John",), ("Mary",)]
