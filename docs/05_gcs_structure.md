# GCS Structure

These are the files created by the codebase in GCS.

```text
cio-bq-load-prod/
├── monthly_checkpoints/
│   ├── {YYYY}_{MM}.done                                        # Example: 2026_03.done
│   └── ...
├── output/
│   ├── worker_chunks/
│   │   ├── corporation/
│   │   │   ├── {worker_id}_{stage}_{run_date}_{uid}.ndjson     # Example: 0_corporation_20260324_6c79615e.ndjson
│   │   │   └── ...
│   │   ├── evaluation_agency/
│   │   │   └── ...
│   │   ├── depot/
│   │   │   └── ...
│   │   └── evaluation/
│   │       └── ...
│   ├── merged/
│   │   ├── corporation/
│   │   │   ├── partial_data_{run_date}_{uid}.ndjson            # Example: partial_data_20260324_123bcf92.ndjson
│   │   │   └── ...
│   │   ├── evaluation_agency/
│   │   │   └── ...
│   │   ├── depot/
│   │   │   └── ...
│   │   └── evaluation/
│   │       └── ...
│   └── staging/
│       ├── corporations_data.ndjson
│       ├── evaluation_agencies_data.ndjson
│       ├── depots_data.ndjson
│       └── evaluations_data.ndjson
├── stage_status/
│   ├── crawl_complete.done                                                                    
│   ├── {stage}_status.json                                     # Example: corporation_status.json                                  
│   └── ...
├── worker_checkpoints/
│   ├── {worker_id}_{stage}_checkpoint.json                     # Example: 0_corporation_checkpoint.json
│   └── ...
└── worker_progress_status/
    ├── {worker_id}_{stage}_progress.done                       # Example: 0_corporation_progress.done
    └── ...
```

## Additional Information

### monthly_checkpoints/*

- **Role:** source of truth for completed monthly extraction runs.

### output/worker_chunks/*

- **Data source:** `local/output/*`
- **Role:** worker-level output.
- **Upload timing:** uploaded from worker's `local/output/` on successful or failed run.
- **Used by:** `merge_ndjson.incremental_merge_chunks()` for `output/merged/*` creation.
- **Merge behavior:**
  - when `drain_all=False`, merging runs only when the number of available chunk files is at least `batch_size`
  - when `drain_all=True`, all remaining chunk files are merged regardless of count
- **Deletion:** after a successful merging of `worker_chunks/*` into `output/merged/*`.

### output/merged/*

- **Data source:** `output/worker_chunks/*`
- **Role:** partially merged worker output.
- **Created by:** `merge_ndjson.incremental_merge_chunks()`.
- **With:** Deduplication by using `data_hash` within each merge operation.
- **Deletion:** once `merge_ndjson.merge_partials_to_final()` finishes merging `output/merged/*` into `output/staging/*`.

### output/staging/*

- **Data source:** `output/merged/*`
- **Role:** source of truth for BigQuery external `staging_*` tables.
- **Created by:** `merge_ndjson.merge_partials_to_final()`.
- **With:** Deduplication by using `data_hash` across all partial files.

### stage_status/*

- **Role:** stores stage-level status files and the crawl completion marker.
- **Contains:**
  - `*_status.json` files used by the Make Webhook Trigger for **Fukunavi (Slack Notifier)**
  - `crawl_complete.done`, used by the Make Webhook Trigger for **Fukunavi (Data Manipulation & Cleanup)**
- **Deletion:** by the **GCS Delete an Object** module in **Fukunavi (Data Manipulation & Cleanup)**.

### worker_progress_status/*

- **Role:** worker-level completion markers.
- **Purpose:** tracks whether a worker has already completed its assigned stage.
- **Deletion:** after a successful stage run.

### worker_checkpoints/*

- **Role:** source of truth for worker resume state.
- **Purpose:** stores each worker's latest traversal position for checkpoint/resume logic.
- **Deletion:** after a successful stage run.
