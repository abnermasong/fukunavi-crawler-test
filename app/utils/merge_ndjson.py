import json
import uuid
from datetime import UTC, datetime

from app.config import GCS_STORAGE
from app.utils.loggers import log


def _iter_ndjson_records(blob):
    """
    Parse NDJSON blob and yield parsed JSON values.

    Skips empty lines and invalid JSON gracefully.
    """

    data = blob.download_as_text()

    for line in data.splitlines():
        if not line.strip():
            continue  # Skip empty lines

        try:
            yield json.loads(line)
        except Exception as e:  # noqa: BLE001 - Ruff does not recognize our custom loggers.py
            log(
                f"Skipping malformed JSON in {blob.name}: {e}",
                component=__name__,
            )


def _serialize_ndjson(records: list[dict]) -> str:
    """
    Serialize list of records to NDJSON format.

    Returns empty string if no records.
    """

    if not records:
        return ""
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n"


def incremental_merge_chunks(
    stage_name: str, *, batch_size: int = 4, drain_all: bool = False
) -> bool:
    """
    Incrementally merge chunk files into partial files with dedup and cleanup.

    Returns True if merge happened, False if skipped.
    """

    chunk_prefix = f"output/worker_chunks/{stage_name}/"

    # STEP 1: Fetch available chunks from GCS
    blobs = sorted(GCS_STORAGE.list_blobs(chunk_prefix), key=lambda b: b.name)

    if not blobs:
        return False  # Nothing to merge

    # STEP 2: Determine which chunks to merge
    # CASE A: drain_all=True → merge all available chunks (final cleanup)
    # CASE B: drain_all=False → only merge if we have enough chunks (incremental merge)
    if drain_all:
        target_blobs = blobs
    else:
        if len(blobs) < batch_size:
            return False  # Not enough chunks yet, wait for more
        target_blobs = blobs[:batch_size]

    seen_hashes = set()
    merged_records: list[dict] = []

    # STEP 3: Merge chunks with deduplication (within this batch)
    for blob in target_blobs:
        for record in _iter_ndjson_records(blob):
            data_hash = record.get("data_hash")

            if data_hash:
                if data_hash in seen_hashes:
                    continue  # Skip duplicate
                seen_hashes.add(data_hash)

            merged_records.append(record)

    if not merged_records:
        return False  # No valid records to merge

    # STEP 4: Generate unique filename for merged partial file
    run_date = datetime.now(UTC).strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:8]

    partial_path = f"output/merged/{stage_name}/partial_data_{run_date}_{uid}.ndjson"

    # STEP 5: Upload merged data to GCS
    GCS_STORAGE.upload_text(
        _serialize_ndjson(merged_records),
        partial_path,
        content_type="application/x-ndjson",
    )

    # STEP 6: Cleanup - delete source chunks after successful merge
    for blob in target_blobs:
        try:
            blob.delete()
        except Exception as e:  # noqa: BLE001 - Ruff does not recognize our custom loggers.py
            log(
                f"[{stage_name}] Failed to delete source chunk {blob.name}: "
                f"[{type(e).__name__}]: {e}",
                component=__name__,
            )

    return True  # Merge completed successfully


def merge_partials_to_final(stage_name: str, output_filename: str):
    """
    Merge all partial files into final staging file with global deduplication.

    Deletes partial files after successful upload.
    """

    prefix = f"output/merged/{stage_name}/"

    # STEP 1: Fetch all partial files from GCS
    blobs = sorted(GCS_STORAGE.list_blobs(prefix), key=lambda b: b.name)

    if not blobs:
        return  # No partials to merge

    seen_hashes = set()
    merged_records: list[dict] = []

    # STEP 2: Merge all partials with global deduplication
    for blob in blobs:
        for record in _iter_ndjson_records(blob):
            data_hash = record.get("data_hash")

            if data_hash:
                if data_hash in seen_hashes:
                    continue  # Skip duplicate across all partials
                seen_hashes.add(data_hash)

            merged_records.append(record)

    # STEP 3: Upload final staging file
    GCS_STORAGE.upload_text(
        _serialize_ndjson(merged_records),
        f"output/staging/{output_filename}",
        content_type="application/x-ndjson",
    )

    # STEP 4: Cleanup - delete partials AFTER successful upload
    for blob in blobs:
        try:
            blob.delete()
        except Exception as e:  # noqa: BLE001 - Ruff does not recognize our custom loggers.py
            log(
                f"[{stage_name}] Failed to delete merged partial {blob.name}: "
                f"[{type(e).__name__}]: {e}",
                component=__name__,
            )
