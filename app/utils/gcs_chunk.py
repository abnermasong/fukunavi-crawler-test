import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.config import GCS_STORAGE


def upload_chunk(stage_name: str, worker_id: int, worker_output_file: str):
    """
    Uploads a chunk of data to Google Cloud Storage every time a worker finishes or fails.

    Will be merged later by the merge stage with dedup logic.
    """

    output_path = Path("output") / worker_output_file

    if not output_path.exists():
        return

    if output_path.stat().st_size == 0:
        return

    run_date = datetime.now(UTC).strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:8]

    gcs_path = f"output/worker_chunks/{stage_name}/{worker_id}_{stage_name}_{run_date}_{uid}.ndjson"

    GCS_STORAGE.upload_file(str(output_path), gcs_path)
