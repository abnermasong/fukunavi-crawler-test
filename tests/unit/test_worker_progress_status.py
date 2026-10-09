from app.utils.worker_progress_status import WorkerProgressStatusManager


def test_worker_progress_status_manager_sets_default_done_file_path():
    """Verify that the default file path uses the .done extension."""
    worker_progress_manager = WorkerProgressStatusManager("example_task")

    assert (
        worker_progress_manager.file_path == "worker_progress_status/example_task.done"
    )


def test_worker_progress_status_manager_allows_custom_extension():
    """Verify that the file path uses the provided custom extension."""
    worker_progress_manager = WorkerProgressStatusManager(
        "example_task", extension="json"
    )

    assert (
        worker_progress_manager.file_path == "worker_progress_status/example_task.json"
    )


def test_worker_progress_status_manager_is_completed_returns_gcs_exists_result(
    monkeypatch,
    mock_gcs,
):
    """Verify that is_completed returns the GCS exists result for the status file."""
    mock_gcs.exists.return_value = True
    monkeypatch.setattr("app.utils.worker_progress_status.GCS_STORAGE", mock_gcs)

    worker_progress_manager = WorkerProgressStatusManager("example_task")

    result = worker_progress_manager.is_completed()

    assert result is True
    mock_gcs.exists.assert_called_once_with("worker_progress_status/example_task.done")


def test_worker_progress_status_manager_mark_completed_uploads_worker_completion_text(
    monkeypatch,
    mock_gcs,
):
    """Verify that mark_completed uploads the expected worker completion text."""
    monkeypatch.setattr("app.utils.worker_progress_status.GCS_STORAGE", mock_gcs)

    worker_progress_manager = WorkerProgressStatusManager("example_task")

    worker_progress_manager.mark_completed(worker_id=2)

    mock_gcs.upload_text.assert_called_once()

    call_args = mock_gcs.upload_text.call_args
    uploaded_text = call_args.args[0]
    uploaded_path = call_args.args[1]
    uploaded_content_type = call_args.kwargs["content_type"]

    assert uploaded_text == "Worker 2 completed"
    assert uploaded_path == "worker_progress_status/example_task.done"
    assert uploaded_content_type == "text/plain"


def test_worker_progress_status_manager_clear_deletes_status_file(
    monkeypatch, mock_gcs
):
    """Verify that clear deletes the worker progress status file."""
    monkeypatch.setattr("app.utils.worker_progress_status.GCS_STORAGE", mock_gcs)

    worker_progress_manager = WorkerProgressStatusManager("example_task")

    worker_progress_manager.clear_progress()

    mock_gcs.delete_object.assert_called_once_with(
        "worker_progress_status/example_task.done"
    )
