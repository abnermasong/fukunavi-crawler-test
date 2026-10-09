import json
from datetime import datetime

from app.config import GCS_STORAGE


def _count_ndjson_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def write_stage_state(
    *,
    stage: str,
    status: str,
    time_started: datetime,
    time_ended: datetime,
    recorded_data_count: int = 0,
    error_message: str = "",
) -> None:
    """
    Overwrites the latest stage state in GCS.

    Single source of truth file per stage.
    """

    payload = {
        "stage": stage,
        "time_started": time_started.isoformat(),
        "time_ended": time_ended.isoformat(),
        "recorded_data_count": recorded_data_count,
        "status": status,
        "error_message": error_message,
    }

    GCS_STORAGE.upload_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        f"stage_status/{stage}_status.json",
        content_type="application/json",
    )


def count_merged_output_lines(output_filename: str) -> int:
    """
    Count records from the final merged NDJSON in GCS.

    Example:
    - output_filename = 'corporations_data.ndjson'
    - reads: output/staging/corporations_data.ndjson
    """

    text = GCS_STORAGE.download_text(f"output/staging/{output_filename}")

    if not text:
        return 0

    return _count_ndjson_lines(text)
