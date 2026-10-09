import json
from pathlib import Path

from app.utils.ndjson import append_ndjson, start_ndjson_file


def test_start_ndjson_file_creates_output_dir_and_returns_file_path(
    monkeypatch, tmp_path
):
    """Verify that start_ndjson_file creates the output directory and returns the created file path."""
    monkeypatch.chdir(tmp_path)

    file_path = start_ndjson_file("test.ndjson")

    assert file_path == Path("output") / "test.ndjson"
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == ""


def test_start_ndjson_file_truncates_existing_file(monkeypatch, tmp_path):
    """Verify that start_ndjson_file truncates an existing NDJSON file before returning it."""
    monkeypatch.chdir(tmp_path)

    output_dir = Path("output")
    output_dir.mkdir()
    existing_file = output_dir / "test.ndjson"
    existing_file.write_text("ABCD", encoding="utf-8")

    assert existing_file.read_text(encoding="utf-8") == "ABCD"

    file_path = start_ndjson_file("test.ndjson")

    assert file_path == existing_file
    assert file_path.read_text(encoding="utf-8") == ""


def test_append_ndjson_creates_output_dir_and_appends_single_record(
    monkeypatch, tmp_path, corporation_record
):
    """Verify that append_ndjson creates the output directory and appends a single record in NDJSON format."""
    monkeypatch.chdir(tmp_path)

    record = corporation_record.copy()

    append_ndjson(record, "test.ndjson")

    file_path = Path("output") / "test.ndjson"
    assert file_path.exists()

    lines = file_path.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == {
        "corporation_name": "社会福祉法人養和会",
        "corporation_type": "社会福祉法人",
        "address": "100-1401   東京都八丈島八丈町大賀郷7670番1号",
        "phone_number": "04996-2-0770",
        "update_date": "2013年10月2日",
        "source_url": "https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=401201001&SVCSBR_CD=001",
        "created_at": "2026-03-03T07:54:45.447545+00:00",
        "data_hash": "9eec2371d36196a7c6082aa54046607156e9f7e4216a26e8faa79bcc266ee325",
    }


def test_append_ndjson_appends_multiple_records_in_order(
    monkeypatch, tmp_path, corporation_record
):
    """Verify that append_ndjson appends multiple records in order using one JSON object per line."""
    monkeypatch.chdir(tmp_path)

    record1 = corporation_record.copy()
    record2 = corporation_record.copy()
    record2["corporation_name"] = "Corporation Number Two"

    append_ndjson(record1, "test.ndjson")
    append_ndjson(record2, "test.ndjson")

    file_path = Path("output") / "test.ndjson"
    lines = file_path.read_text(encoding="utf-8").splitlines()

    assert json.loads(lines[0]) == {
        "corporation_name": "社会福祉法人養和会",
        "corporation_type": "社会福祉法人",
        "address": "100-1401   東京都八丈島八丈町大賀郷7670番1号",
        "phone_number": "04996-2-0770",
        "update_date": "2013年10月2日",
        "source_url": "https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=401201001&SVCSBR_CD=001",
        "created_at": "2026-03-03T07:54:45.447545+00:00",
        "data_hash": "9eec2371d36196a7c6082aa54046607156e9f7e4216a26e8faa79bcc266ee325",
    }
    assert json.loads(lines[1]) == {
        "corporation_name": "Corporation Number Two",
        "corporation_type": "社会福祉法人",
        "address": "100-1401   東京都八丈島八丈町大賀郷7670番1号",
        "phone_number": "04996-2-0770",
        "update_date": "2013年10月2日",
        "source_url": "https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=401201001&SVCSBR_CD=001",
        "created_at": "2026-03-03T07:54:45.447545+00:00",
        "data_hash": "9eec2371d36196a7c6082aa54046607156e9f7e4216a26e8faa79bcc266ee325",
    }
