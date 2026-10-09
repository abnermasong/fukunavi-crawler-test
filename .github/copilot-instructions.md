
# Copilot instructions — fukunavi-crawler

This repo crawls public data from Fukunavi and exports it as NDJSON to GCS, manipulates it in BigQuery, and visualizes it in Looker Studio. The crawler is scheduled via Render Cron Jobs.

## Documentation 

- `docs/01_project_overview.md`: project background, objectives, technologies used, trigger conditions, and process overview
- `docs/02_database_structure.md`: schema and relationships
- `docs/03_fukunavi_data_count.md`: number of data to be extracted from Fukunavi (for scope understanding)
- `docs/04_fukunavi_navigation_and_data_location.md`: note on crawler navigation and where the relevant data is located on Fukunavi website
- `docs/05_gcs_structure.md`: tree structure of objects created and used in GCS
- `docs/06_bigquery_integration.md`: details on logic for BigQuery data manipulation and transformation after crawl completion
- `docs/07_make_integration.md`: details on how Make.com is integrated for orchestration after crawl completion

## Technologies used

- Python 3.12 (project in `pyproject.toml`)
- Playwright (async) → crawling
- Render cron job → scheduling and execution
- Google Cloud Storage (GCS) → persistent storage
- BigQuery → data warehousing and transformation
- Looker Studio → visualization
- Make.com → orchestration after crawl completion
- GCS Notifications (Pub/Sub) → trigger Make.com webhook on crawl completion

## Current flow

1. Render Cron Job triggers `uv run python -u -m app.main` 
2. Crawlers run in parallel (limited to 2 workers) and writes to GCS
	- `monthly_checkpoints/YYYY_MM.done` → written after successful monthly crawl completion, source of truth for completed monthly data extraction
	- `output/worker_chunks/{stage_name}/{worker_id}_{stage}_{run_date}_{uid}.ndjson` →  uploaded `app/output/*` to GCS incrementally after crawling, both successful and failed runs. Deleted after `worker_chunks/` → `merged/`
	- `output/merged/{stage_name}/partial_data_{run_date}_{uid}.ndjson` → merged data from `worker_chunks/` according to `batch_size`. Deleted after `merged/` → `staging/`
	- `output/staging/corporations_data.ndjson`, `output/staging/evaluation_agencies_data.ndjson`, `output/staging/depots_data.ndjson`, `output/staging/evaluations_data.ndjson` → source of truth for BQ external tables `staging_*`
	- `stage_status/crawl_complete.done` → written after all stages complete, triggers Make.com webhook for post-crawl data manipulation and cleanup
	- `stage_status/{stage_name}_status.json` → written after a successful stage completion, triggers Make.com webhook for slack notification integration
	- `worker_checkpoints/{worker_id}_{stage}_checkpoint.json` → written incrementally during crawling, source of truth for crawl progress and resume logic. Deleted on successful run
	- `worker_progress_status/{worker_id}_{stage}_progress.done` → written after a worker completes its assigned crawl, worker-level complete flag. Deleted on successful run
3. Make.com webhook triggered by `stage_status/{stage_name}_status.json` → sends a Slack notification for stage-level completion
4. Make.com webhook triggered by `stage_status/crawl_complete.done` → executes data manipulation for `core_*` tables using BigQuery `Run A Query Module` → `BigQuery Procedure (corporations → evaluation_agencies → depots → evaluations data manipulation)` then cleanup GCS content to ensure fresh start for succeeding months, then sends a Slack notification on completion
5. BigQuery `core_*` tables are used as source for Looker Studio visualization

## Change policy

- Keep Playwright crawlers as-is unless the change is explicitly requested.
	- Crawlers are already stable and have completed test runs.
	- Changes to crawlers can easily cause unintended consequences and break the flow, so they should be avoided unless necessary.

## Development guidelines

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

### Project-specific constraints

- Ensure new features are backwards compatible and do not break existing functionality.
- Do not increase worker count or remove random sleeps/checkpointing.
- Do not rename/move the GCS marker objects without updating Render/Make.com configuration.
- If a change might break Make.com / BigQuery / GCS integration, call it out explicitly.

### Code style

- Follow PEP 8 import standards (https://peps.python.org/pep-0008/#imports):
  - Group imports in three sections separated by blank lines:
    1. Standard library imports
    2. Third-party imports (e.g., playwright, dotenv, google.cloud)
    3. Local application imports (e.g., app.config, app.utils, app.services)
  - Within each group, list all `import` statements first (sorted alphabetically), then all `from ... import` statements (sorted alphabetically)
  - Use absolute imports for clarity

