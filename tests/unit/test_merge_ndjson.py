import json

from app.utils.merge_ndjson import incremental_merge_chunks, merge_partials_to_final


def test_incremental_merge_chunks_returns_false_when_no_chunks_exist(
    monkeypatch, mock_gcs
):
    """Verify that incremental_merge_chunks returns False when no chunk blobs exist."""
    mock_gcs.list_blobs.return_value = []
    monkeypatch.setattr("app.utils.merge_ndjson.GCS_STORAGE", mock_gcs)

    result = incremental_merge_chunks("example_stage")

    assert result is False
    mock_gcs.upload_text.assert_not_called()


def test_incremental_merge_chunks_returns_false_when_chunks_are_less_than_batch_size(
    monkeypatch, mock_gcs, create_mock_ndjson_file
):
    """Verify that incremental_merge_chunks returns False when available chunks are fewer than the batch size."""
    chunk1 = create_mock_ndjson_file(
        name="output/worker_chunks/example_stage/chunk1.ndjson", records=[]
    )

    chunk2 = create_mock_ndjson_file(
        name="output/worker_chunks/example_stage/chunk2.ndjson", records=[]
    )

    mock_gcs.list_blobs.return_value = [chunk1, chunk2]
    monkeypatch.setattr("app.utils.merge_ndjson.GCS_STORAGE", mock_gcs)

    result = incremental_merge_chunks("example_stage", batch_size=3)

    assert result is False
    mock_gcs.upload_text.assert_not_called()
    chunk1.delete.assert_not_called()
    chunk2.delete.assert_not_called()


def test_incremental_merge_chunks_uploads_deduplicated_merged_records(
    monkeypatch, mock_gcs, corporation_record, create_mock_ndjson_file
):
    """Verify that incremental_merge_chunks uploads deduplicated merged records."""
    record1 = corporation_record.copy()

    record2 = corporation_record.copy()
    record2["corporation_name"] = "Corporation Number Two"
    record2["data_hash"] = "hash-2"

    duplicated_record = corporation_record.copy()

    chunk1 = create_mock_ndjson_file(
        name="output/worker_chunks/example_stage/chunk1.ndjson",
        records=[record1, record2],
    )

    chunk2 = create_mock_ndjson_file(
        name="output/worker_chunks/example_stage/chunk2.ndjson",
        records=[duplicated_record],
    )

    mock_gcs.list_blobs.return_value = [chunk1, chunk2]
    monkeypatch.setattr("app.utils.merge_ndjson.GCS_STORAGE", mock_gcs)

    result = incremental_merge_chunks("example_stage", batch_size=2)

    assert result is True
    mock_gcs.upload_text.assert_called_once()

    call_args = mock_gcs.upload_text.call_args
    uploaded_text = call_args.args[0]
    uploaded_path = call_args.args[1]

    uploaded_lines = uploaded_text.splitlines()

    assert len(uploaded_lines) == 2
    assert json.loads(uploaded_lines[0]) == record1
    assert json.loads(uploaded_lines[1]) == record2
    assert uploaded_path.startswith("output/merged/example_stage/partial_data_")
    assert uploaded_path.endswith(".ndjson")


def test_incremental_merge_chunks_deletes_processed_chunks(
    monkeypatch, mock_gcs, corporation_record, create_mock_ndjson_file
):
    """Verify that incremental_merge_chunks deletes processed chunk blobs after upload."""
    record = corporation_record.copy()

    chunk1 = create_mock_ndjson_file(
        name="output/worker_chunks/example_stage/chunk_1.ndjson",
        records=[record],
    )

    chunk2 = create_mock_ndjson_file(
        name="output/worker_chunks/example_stage/chunk_2.ndjson",
        records=[record],
    )

    mock_gcs.list_blobs.return_value = [chunk1, chunk2]
    monkeypatch.setattr("app.utils.merge_ndjson.GCS_STORAGE", mock_gcs)

    result = incremental_merge_chunks("example_stage", batch_size=2)

    assert result is True
    chunk1.delete.assert_called_once()
    chunk2.delete.assert_called_once()


def test_incremental_merge_chunks_uses_all_chunks_when_drain_all_is_true(
    monkeypatch, mock_gcs, corporation_record, create_mock_ndjson_file
):
    """Verify that incremental_merge_chunks processes all available chunks when drain_all is True."""
    record1 = corporation_record.copy()

    record2 = corporation_record.copy()
    record2["corporation_name"] = "Corporation Number Two"
    record2["data_hash"] = "hash-2"

    chunk1 = create_mock_ndjson_file(
        name="output/worker_chunks/example_stage/chunk_1.ndjson",
        records=[record1],
    )

    chunk2 = create_mock_ndjson_file(
        name="output/worker_chunks/example_stage/chunk_2.ndjson",
        records=[record2],
    )

    mock_gcs.list_blobs.return_value = [chunk1, chunk2]
    monkeypatch.setattr("app.utils.merge_ndjson.GCS_STORAGE", mock_gcs)

    result = incremental_merge_chunks("example_stage", batch_size=10, drain_all=True)

    assert result is True
    mock_gcs.upload_text.assert_called_once()
    chunk1.delete.assert_called_once()
    chunk2.delete.assert_called_once()

    call_args = mock_gcs.upload_text.call_args
    uploaded_text = call_args.args[0]
    uploaded_lines = uploaded_text.splitlines()

    assert len(uploaded_lines) == 2
    assert json.loads(uploaded_lines[0]) == record1
    assert json.loads(uploaded_lines[1]) == record2


def test_merge_partials_to_final_returns_none_when_no_partial_blobs_exist(
    monkeypatch, mock_gcs
):
    """Verify that merge_partials_to_final returns without uploading when no partial blobs exist."""
    mock_gcs.list_blobs.return_value = []
    monkeypatch.setattr("app.utils.merge_ndjson.GCS_STORAGE", mock_gcs)

    result = merge_partials_to_final("example_stage", "example_data.ndjson")

    assert result is None
    mock_gcs.upload_text.assert_not_called()


def test_merge_partials_to_final_uploads_deduplicated_merged_records(
    monkeypatch, mock_gcs, corporation_record, create_mock_ndjson_file
):
    """Verify that merge_partials_to_final uploads deduplicated merged records."""
    record1 = corporation_record.copy()

    record2 = corporation_record.copy()
    record2["corporation_name"] = "Corporation Number Two"
    record2["data_hash"] = "hash-2"

    duplicated_record = corporation_record.copy()

    partial1 = create_mock_ndjson_file(
        name="output/merged/example_stage/partial_1.ndjson",
        records=[record1, record2],
    )

    partial2 = create_mock_ndjson_file(
        name="output/merged/example_stage/partial_2.ndjson",
        records=[duplicated_record],
    )

    mock_gcs.list_blobs.return_value = [partial1, partial2]
    monkeypatch.setattr("app.utils.merge_ndjson.GCS_STORAGE", mock_gcs)

    merge_partials_to_final("example_stage", "example_data.ndjson")

    mock_gcs.upload_text.assert_called_once()

    call_args = mock_gcs.upload_text.call_args
    uploaded_text = call_args.args[0]
    uploaded_path = call_args.args[1]

    uploaded_lines = uploaded_text.splitlines()

    assert len(uploaded_lines) == 2
    assert json.loads(uploaded_lines[0]) == record1
    assert json.loads(uploaded_lines[1]) == record2
    assert uploaded_path == "output/staging/example_data.ndjson"


def test_merge_partials_to_final_deletes_processed_partials(
    monkeypatch, mock_gcs, corporation_record, create_mock_ndjson_file
):
    """Verify that merge_partials_to_final deletes processed partial blobs after upload."""
    record = corporation_record.copy()

    partial1 = create_mock_ndjson_file(
        name="output/merged/example_stage/partial_1.ndjson",
        records=[record],
    )

    partial2 = create_mock_ndjson_file(
        name="output/merged/example_stage/partial_2.ndjson",
        records=[record],
    )

    mock_gcs.list_blobs.return_value = [partial1, partial2]
    monkeypatch.setattr("app.utils.merge_ndjson.GCS_STORAGE", mock_gcs)

    merge_partials_to_final("example_stage", "example_data.ndjson")

    partial1.delete.assert_called_once()
    partial2.delete.assert_called_once()
