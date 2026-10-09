from pathlib import Path

from app.utils.gcs_chunk import upload_chunk


def test_upload_chunk_returns_without_upload_when_worker_output_file_does_not_exist(
    monkeypatch, mock_gcs, tmp_path
):
    """Verify that upload_chunk returns without uploading when the worker output file does not exist."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("app.utils.gcs_chunk.GCS_STORAGE", mock_gcs)

    upload_chunk(
        stage_name="example_stage",
        worker_id=1,
        worker_output_file="example_data.ndjson",
    )

    mock_gcs.upload_file.assert_not_called()


def test_upload_chunk_returns_without_upload_when_worker_output_file_is_empty(
    monkeypatch, mock_gcs, tmp_path
):
    """Verify that upload_chunk returns without uploading when the worker output file is empty."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("app.utils.gcs_chunk.GCS_STORAGE", mock_gcs)

    output_dir = Path("output")
    output_dir.mkdir()
    worker_output_file = output_dir / "example_data.ndjson"
    worker_output_file.write_text("", encoding="utf-8")

    upload_chunk(
        stage_name="example_stage",
        worker_id=1,
        worker_output_file="example_data.ndjson",
    )

    mock_gcs.upload_file.assert_not_called()


def test_upload_chunk_uploads_worker_output_file_to_worker_chunk_gcs_path(
    monkeypatch, mock_gcs, tmp_path
):
    """Verify that upload_chunk uploads the worker output file to a worker chunk GCS path."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("app.utils.gcs_chunk.GCS_STORAGE", mock_gcs)

    output_dir = Path("output")
    output_dir.mkdir()
    worker_output_file = output_dir / "example_data.ndjson"
    worker_output_file.write_text('{"a": 1}\n', encoding="utf-8")

    upload_chunk(
        stage_name="example_stage",
        worker_id=1,
        worker_output_file="example_data.ndjson",
    )

    mock_gcs.upload_file.assert_called_once()

    call_args = mock_gcs.upload_file.call_args
    uploaded_output_path = call_args.args[0]
    uploaded_gcs_path = call_args.args[1]

    assert Path(uploaded_output_path) == Path("output") / "example_data.ndjson"
    assert uploaded_gcs_path.startswith(
        "output/worker_chunks/example_stage/1_example_stage_"
    )
    assert uploaded_gcs_path.endswith(".ndjson")
