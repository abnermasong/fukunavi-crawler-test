from app.config import GCS_STORAGE


class WorkerProgressStatusManager:
    def __init__(self, progress_file_name: str, extension: str = "done"):
        self._gcs = GCS_STORAGE
        self.file_path = f"worker_progress_status/{progress_file_name}.{extension}"

    def is_completed(self) -> bool:
        """
        Checks if the progress status for the worker in that stage is completed.
        """

        return self._gcs.exists(self.file_path)

    def mark_completed(self, worker_id: int) -> None:
        """
        Marks the progress status for the worker in that stage as completed.
        """

        self._gcs.upload_text(
            f"Worker {worker_id} completed", self.file_path, content_type="text/plain"
        )

    def clear_progress(self) -> None:
        """
        Clears the progress status for the worker in that stage.
        """

        self._gcs.delete_object(self.file_path)
