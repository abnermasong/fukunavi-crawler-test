import asyncio
import json
import traceback
from datetime import UTC, datetime

from app.config import GCS_STORAGE, MAX_RUNTIME_SECONDS, WORKER_COUNT
from app.constants import CORPORATION_AGENCY_AREA_CODES
from app.services.corporations_crawler import CorporationCrawler
from app.services.depots_crawler import DepotCrawler
from app.services.evaluation_agencies_crawler import EvaluationAgencyCrawler
from app.services.evaluations_crawler import EvaluationCrawler
from app.utils.browser import BrowserManager
from app.utils.cancellation import (
    CancellationFlagManager,
    GracefulShutdownRequestedException,
)
from app.utils.checkpoint import CheckpointManager
from app.utils.gcs_chunk import upload_chunk
from app.utils.loggers import format_duration, log
from app.utils.merge_ndjson import incremental_merge_chunks, merge_partials_to_final
from app.utils.partition import partition
from app.utils.runtime_guard import RuntimeGuardManager, RuntimeLimitReachedException
from app.utils.stage_progress_status import count_merged_output_lines, write_stage_state
from app.utils.worker_progress_status import WorkerProgressStatusManager


async def run_stage(
    *,
    runtime_guard: RuntimeGuardManager,
    stage_name: str,
    crawler_class,
    partition_values: list[str] | None,
    staging_filename: str,
) -> bool:

    log(
        f"Starting crawler: {stage_name}",
        component=__name__,
    )

    stage_start_time = datetime.now(UTC)
    stage_status_marker = f"stage_status/{stage_name}_status.json"

    if GCS_STORAGE.exists(stage_status_marker):
        raw = GCS_STORAGE.download_text(stage_status_marker)

        if raw:
            data = json.loads(raw)
            if data.get("status") == "success":
                log(
                    f"Data extraction for {stage_name} has already been completed. Skipping",
                    component=__name__,
                )
                return False

    # Drain any existing chunks from previous runs before starting new workers
    while incremental_merge_chunks(stage_name):
        log(
            f"[{stage_name}] Merging existing extracted data before starting workers",
            component=__name__,
        )

    # Determine partitions
    if partition_values is not None:
        partitions = partition(partition_values, WORKER_COUNT)

        for worker_id, subset in enumerate(partitions):
            log(
                f"[{stage_name}] Worker #{worker_id} has been assigned {len(subset)} area codes: {subset}",
                component=__name__,
            )
    else:
        partitions = [None] * WORKER_COUNT

    # Create shared cancellation flag for cooperative shutdown
    cancellation_flag = CancellationFlagManager()

    runtime_exceeded = False
    stage_failed = False
    first_error_message = ""

    async def worker(worker_id: int, partition_subset):
        worker_start_time = datetime.now(UTC)

        worker_status = WorkerProgressStatusManager(
            f"{worker_id}_{stage_name}_progress"
        )

        if worker_status.is_completed():
            log(
                f"[{stage_name}] Worker #{worker_id} has already finished extracting data. Skipping",
                component=__name__,
            )

            log(
                f"[WORKER SUMMARY] [{stage_name} - Worker #{worker_id}] Already finished extracting data.",
                component=__name__,
            )

            return False

        worker_output_file = f"{stage_name}_worker_{worker_id}.ndjson"

        crawler = crawler_class(
            worker_id=worker_id,
            worker_count=WORKER_COUNT,
            runtime_guard=runtime_guard,
            cancellation_flag=cancellation_flag,
        )

        try:
            async with BrowserManager(headless=True) as browser_context:
                if partition_subset is not None:
                    # Evaluation agency receives pre-partitioned area codes from main
                    await crawler.crawl(
                        browser_context,
                        output_file=worker_output_file,
                        target_area_codes=partition_subset,
                    )
                else:
                    # Depot and evaluation stages have their partitioning logic inside the crawler, so main just passes None
                    await crawler.crawl(
                        browser_context,
                        output_file=worker_output_file,
                    )

            worker_status.mark_completed(worker_id=worker_id)
            log(
                f"[{stage_name}] Worker #{worker_id} completed successfully.",
                component=__name__,
            )

        except GracefulShutdownRequestedException:
            log(
                f"[{stage_name}] Stopping worker #{worker_id} due to an error that occurred in another worker",
                component=__name__,
            )

        except RuntimeLimitReachedException:
            nonlocal runtime_exceeded
            runtime_exceeded = True

            log(
                f"[{stage_name}] Worker #{worker_id} runtime limit has been reached.",
                component=__name__,
            )
            cancellation_flag.request_shutdown()

        except Exception as e:  # noqa: BLE001 - Ruff does not recognize our custom loggers.py
            nonlocal stage_failed, first_error_message
            stage_failed = True

            error_summary = f"[{type(e).__name__}]: {e}"
            error_traceback = traceback.format_exc()

            # Slack message: Short but informative error message for alerting purposes
            if first_error_message == "":
                first_error_message = error_summary

            # Render Cron Job log: Traceable error log for debugging purposes
            log(
                f"[{stage_name}] Worker #{worker_id} failed with error:\n{error_traceback}",
                component=__name__,
            )
            cancellation_flag.request_shutdown()

        finally:
            records_count = len(crawler.records)

            worker_end_time = datetime.now(UTC)
            worker_duration = format_duration(worker_start_time, worker_end_time)

            log(
                f"[WORKER SUMMARY] [{stage_name} - Worker #{worker_id}] Data Extracted: {records_count} Duration: {worker_duration}",
                component=__name__,
            )

            upload_chunk(
                stage_name=stage_name,
                worker_id=worker_id,
                worker_output_file=worker_output_file,
            )

    tasks = [
        asyncio.create_task(worker(worker_id, partitions[worker_id]))
        for worker_id in range(WORKER_COUNT)
    ]

    # Wait for all workers to complete (either successfully or via graceful shutdown)
    await asyncio.gather(*tasks)

    if runtime_exceeded:
        return True

    if stage_failed:
        write_stage_state(
            stage=stage_name,
            status="failed",
            time_started=stage_start_time,
            time_ended=datetime.now(UTC),
            error_message=first_error_message,
        )
        return True

    # Success path
    while incremental_merge_chunks(stage_name):
        log(f"[{stage_name}] Merging extracted data", component=__name__)

    # Ensure there's no leftover chunks that is not included by batch size
    if incremental_merge_chunks(stage_name, drain_all=True):
        log(
            f"[{stage_name}] Merging all remaining extracted data into a single file",
            component=__name__,
        )

    merge_partials_to_final(stage_name, f"{staging_filename}.ndjson")
    log(
        f"[{stage_name}] Merging all extracted data into a final staging data",
        component=__name__,
    )

    final_count = count_merged_output_lines(f"{staging_filename}.ndjson")

    write_stage_state(
        stage=stage_name,
        status="success",
        time_started=stage_start_time,
        time_ended=datetime.now(UTC),
        recorded_data_count=final_count,
    )

    log(f"[{stage_name}] Cleaning checkpoints and worker markers", component=__name__)

    for worker_id in range(WORKER_COUNT):
        CheckpointManager(f"{worker_id}_{stage_name}_checkpoint").clear_progress()
        WorkerProgressStatusManager(
            f"{worker_id}_{stage_name}_progress"
        ).clear_progress()

    log(
        f"[{stage_name}] Data extraction completed successfully with {final_count} records.",
        component=__name__,
    )

    return False


async def main():

    runtime_guard = RuntimeGuardManager(MAX_RUNTIME_SECONDS)

    now = datetime.now(UTC)
    month_complete_marker = f"monthly_checkpoints/{now.year}_{now.month:02d}.done"

    if GCS_STORAGE.exists(month_complete_marker):
        log(
            f"Data extraction for {now.year}-{now.month:02d} has already been completed. Skipping",
            component=__name__,
        )
        return

    if await run_stage(
        runtime_guard=runtime_guard,
        stage_name="corporation",
        crawler_class=CorporationCrawler,
        partition_values=None,
        staging_filename="corporations_data",
    ):
        return

    if await run_stage(
        runtime_guard=runtime_guard,
        stage_name="evaluation_agency",
        crawler_class=EvaluationAgencyCrawler,
        partition_values=CORPORATION_AGENCY_AREA_CODES,
        staging_filename="evaluation_agencies_data",
    ):
        return

    if await run_stage(
        runtime_guard=runtime_guard,
        stage_name="depot",
        crawler_class=DepotCrawler,
        partition_values=None,
        staging_filename="depots_data",
    ):
        return

    if await run_stage(
        runtime_guard=runtime_guard,
        stage_name="evaluation",
        crawler_class=EvaluationCrawler,
        partition_values=None,
        staging_filename="evaluations_data",
    ):
        return

    GCS_STORAGE.upload_text(
        f"Crawl for {now.year}-{now.month:02d} is complete",
        month_complete_marker,
        content_type="text/plain",
    )

    crawl_complete_marker = "stage_status/crawl_complete.done"

    GCS_STORAGE.upload_text(
        "Crawl for all stages is complete",
        crawl_complete_marker,
        content_type="text/plain",
    )

    log("Data extraction for all stages is complete.", component=__name__)


if __name__ == "__main__":
    asyncio.run(main())
