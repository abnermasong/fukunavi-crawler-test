import json

import pytest

from app.utils.checkpoint import CheckpointManager


def test_checkpoint_manager_load_returns_none_when_no_checkpoint_data(
    monkeypatch, mock_gcs
):
    """Verify that load returns None when GCS has no checkpoint data."""
    mock_gcs.download_text.return_value = None
    monkeypatch.setattr("app.utils.checkpoint.GCS_STORAGE", mock_gcs)

    checkpoint_manager = CheckpointManager("example_checkpoint")

    assert checkpoint_manager.load_progress() is None
    mock_gcs.download_text.assert_called_once_with(
        "worker_checkpoints/example_checkpoint.json"
    )


def test_checkpoint_manager_load_returns_parsed_json_when_checkpoint_exists(
    monkeypatch,
    mock_gcs,
):
    """Verify that load returns parsed checkpoint data when valid JSON exists."""
    mock_gcs.download_text.return_value = (
        '{"area_code": "0", "page_num": 51, "row_index": 5}'
    )
    monkeypatch.setattr("app.utils.checkpoint.GCS_STORAGE", mock_gcs)

    checkpoint_manager = CheckpointManager("example_checkpoint")

    assert checkpoint_manager.load_progress() == {
        "area_code": "0",
        "page_num": 51,
        "row_index": 5,
    }
    mock_gcs.download_text.assert_called_once_with(
        "worker_checkpoints/example_checkpoint.json"
    )


def test_checkpoint_manager_load_raises_when_checkpoint_json_is_invalid(
    monkeypatch,
    mock_gcs,
):
    """Verify that load_progress() raises when checkpoint data is invalid JSON."""
    mock_gcs.download_text.return_value = "Invalid JSON data"
    monkeypatch.setattr("app.utils.checkpoint.GCS_STORAGE", mock_gcs)

    checkpoint_manager = CheckpointManager("example_checkpoint")

    with pytest.raises(json.JSONDecodeError):
        checkpoint_manager.load_progress()

    mock_gcs.download_text.assert_called_once_with(
        "worker_checkpoints/example_checkpoint.json"
    )


def test_checkpoint_manager_load_raises_when_checkpoint_json_is_empty(
    monkeypatch,
    mock_gcs,
):
    """Verify that load_progress() raises when checkpoint data is empty."""
    mock_gcs.download_text.return_value = ""
    monkeypatch.setattr("app.utils.checkpoint.GCS_STORAGE", mock_gcs)

    checkpoint_manager = CheckpointManager("example_checkpoint")

    with pytest.raises(json.JSONDecodeError):
        checkpoint_manager.load_progress()

    mock_gcs.download_text.assert_called_once_with(
        "worker_checkpoints/example_checkpoint.json"
    )


def test_checkpoint_manager_save_uploads_json_checkpoint_data(monkeypatch, mock_gcs):
    """Verify that save uploads checkpoint data as JSON with application/json content type."""
    monkeypatch.setattr("app.utils.checkpoint.GCS_STORAGE", mock_gcs)

    checkpoint_manager = CheckpointManager("example_checkpoint")
    crawl_progress = {"area_code": "0", "page_num": 51, "row_index": 5}

    checkpoint_manager.save_progress(crawl_progress)

    mock_gcs.upload_text.assert_called_once()

    call_args = mock_gcs.upload_text.call_args
    uploaded_text = call_args.args[0]
    uploaded_path = call_args.args[1]
    uploaded_content_type = call_args.kwargs["content_type"]

    assert json.loads(uploaded_text) == {
        "area_code": "0",
        "page_num": 51,
        "row_index": 5,
    }
    assert uploaded_path == "worker_checkpoints/example_checkpoint.json"
    assert uploaded_content_type == "application/json"


def test_checkpoint_manager_clear_deletes_checkpoint_file(monkeypatch, mock_gcs):
    """Verify that clear deletes the checkpoint file from GCS."""
    monkeypatch.setattr("app.utils.checkpoint.GCS_STORAGE", mock_gcs)

    checkpoint_manager = CheckpointManager("example_checkpoint")

    checkpoint_manager.clear_progress()

    mock_gcs.delete_object.assert_called_once_with(
        "worker_checkpoints/example_checkpoint.json"
    )
