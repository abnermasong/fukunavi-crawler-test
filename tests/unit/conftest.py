import json
from unittest.mock import Mock

import pytest


@pytest.fixture
def corporation_record() -> dict:
    """Base corporation record for testing."""
    return {
        "corporation_name": "社会福祉法人養和会",
        "corporation_type": "社会福祉法人",
        "address": "100-1401   東京都八丈島八丈町大賀郷7670番1号",
        "phone_number": "04996-2-0770",
        "update_date": "2013年10月2日",
        "source_url": "https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=401201001&SVCSBR_CD=001",
        "created_at": "2026-03-03T07:54:45.447545+00:00",
        "data_hash": "9eec2371d36196a7c6082aa54046607156e9f7e4216a26e8faa79bcc266ee325",
    }


@pytest.fixture
def mock_gcs():
    """Mock GCS storage dependency."""
    return Mock()


@pytest.fixture
def create_mock_ndjson_file():
    """Create a mock NDJSON file object with a name and serialized records."""

    def _create(name: str, records: list[dict] | None = None):
        mock_file = Mock()
        mock_file.name = name  # output/worker_chunks/{stage_name}/{worker_id}_{stage}_{run_date}_{uid}.ndjson | output/merged/{stage_name}/partial_data_{run_date}_{uid}.ndjson

        records = records or []
        mock_file.download_as_text.return_value = (
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
            + "\n"
            if records
            else ""
        )

        return mock_file

    return _create
