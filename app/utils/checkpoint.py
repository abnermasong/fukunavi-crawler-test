import json

from app.config import GCS_STORAGE


class CheckpointManager:
    """
    Manages checkpoint files for crawlers, allowing resumption of interrupted crawls.
    """

    def __init__(self, checkpoint_file_name: str) -> None:
        self._gcs = GCS_STORAGE
        self._path = f"worker_checkpoints/{checkpoint_file_name}.json"

    def load_progress(self) -> dict | None:
        """
        Loads crawler's progress from the checkpoint file.
        """

        data = self._gcs.download_text(self._path)
        if data is None:
            return None

        return json.loads(data)

    def save_progress(self, crawl_progress: dict) -> None:
        """
        Saves crawler's current progress.
        """

        self._gcs.upload_text(
            json.dumps(crawl_progress, ensure_ascii=False),
            self._path,
            content_type="application/json",
        )

    def clear_progress(self) -> None:
        """
        Clears crawler's progress data.
        """

        self._gcs.delete_object(self._path)
