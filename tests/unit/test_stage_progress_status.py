import json
from datetime import UTC, datetime

from app.utils.stage_progress_status import (
    count_merged_output_lines,
    write_stage_state,
)


def test_write_stage_state_uploads_expected_stage_status_json(monkeypatch, mock_gcs):
    """Verify that write_stage_state uploads the expected stage status JSON to GCS."""
    monkeypatch.setattr("app.utils.stage_progress_status.GCS_STORAGE", mock_gcs)

    time_started = datetime(2026, 4, 16, 10, 0, 0, tzinfo=UTC)
    time_ended = datetime(2026, 4, 16, 11, 2, 3, tzinfo=UTC)

    write_stage_state(
        stage="example_stage",
        status="success",
        time_started=time_started,
        time_ended=time_ended,
        recorded_data_count=25,
        error_message="",
    )

    mock_gcs.upload_text.assert_called_once()

    call_args = mock_gcs.upload_text.call_args
    uploaded_text = call_args.args[0]
    uploaded_path = call_args.args[1]
    uploaded_content_type = call_args.kwargs["content_type"]

    assert json.loads(uploaded_text) == {
        "stage": "example_stage",
        "time_started": "2026-04-16T10:00:00+00:00",
        "time_ended": "2026-04-16T11:02:03+00:00",
        "recorded_data_count": 25,
        "status": "success",
        "error_message": "",
    }
    assert uploaded_path == "stage_status/example_stage_status.json"
    assert uploaded_content_type == "application/json"


def test_write_stage_state_uploads_error_message_when_provided(monkeypatch, mock_gcs):
    """Verify that write_stage_state includes the provided error message in the uploaded JSON."""
    monkeypatch.setattr("app.utils.stage_progress_status.GCS_STORAGE", mock_gcs)

    time_started = datetime(2026, 4, 16, 10, 0, 0, tzinfo=UTC)
    time_ended = datetime(2026, 4, 16, 10, 0, 30, tzinfo=UTC)

    write_stage_state(
        stage="example_stage",
        status="failed",
        time_started=time_started,
        time_ended=time_ended,
        error_message="Example error message",
    )

    mock_gcs.upload_text.assert_called_once()

    call_args = mock_gcs.upload_text.call_args
    uploaded_text = call_args.args[0]

    assert json.loads(uploaded_text)["error_message"] == "Example error message"


def test_count_merged_output_lines_returns_zero_when_gcs_file_is_empty(
    monkeypatch, mock_gcs
):
    """Verify that count_merged_output_lines returns 0 when the merged output file is empty."""
    mock_gcs.download_text.return_value = ""
    monkeypatch.setattr("app.utils.stage_progress_status.GCS_STORAGE", mock_gcs)

    result = count_merged_output_lines("example_stage.ndjson")

    assert result == 0
    mock_gcs.download_text.assert_called_once_with(
        "output/staging/example_stage.ndjson"
    )


def test_count_merged_output_lines_counts_non_empty_ndjson_lines(monkeypatch, mock_gcs):
    """Verify that count_merged_output_lines counts only non-empty lines from the merged output file."""
    mock_gcs.download_text.return_value = '{"a": 1}\n\n{"b": 2}\n{"c": 3}\n'
    monkeypatch.setattr("app.utils.stage_progress_status.GCS_STORAGE", mock_gcs)

    result = count_merged_output_lines("example_stage.ndjson")

    assert result == 3
    mock_gcs.download_text.assert_called_once_with(
        "output/staging/example_stage.ndjson"
    )
