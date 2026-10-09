
# fukunavi-crawler

Crawler for public data from Fukunavi. It exports data as NDJSON to GCS and is intended to be orchestrated by Make.com and Render Cron Jobs on a schedule (e.g., monthly). The data are then manipulated in BigQuery and visualized in Looker Studio.

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/smart-study-inc/fukunavi-crawler.git
cd fukunavi-crawler
```

### 2. Install uv

This project uses [uv](https://docs.astral.sh/uv/) as the Python dependency manager.

If you do not have uv installed yet:

```bash
# Install uv (python package manager)
$ brew install uv
# or
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Configure .env

### 4. Run

```bash
uv sync
playwright install # run once or every new version is merged
gcloud auth application-default login # authentication is required to upload file in GCS
uv run python -m app.main
```

## Testing

### <ins> Unit Test </ins>

```bash
uv sync # pytest
uv run pytest tests/unit -v
```

**Target:**

- `app/utils/*`

### <ins> E2E Test</ins>

- Navigation tests → `tests/e2e/sync/*`
- Data extraction tests → `test/e2e/async/*`

### <ins> Navigation Tests (synchronous) </ins>

```bash
uv sync # pytest-playwright
uv run pytest tests/e2e/sync -v --slowmo=1000
```

**Important flags:**

- `-v` → verbose testing
- `--slowmo=1000` → slows down navigation. Very important to avoid bot-like behavior, increase when test fails due to slow site or heavy traffic
- `--tracing=on` → for debugging, upload trace file to <https://trace.playwright.dev/>
- `--headed` → show browser when testing

**Target:**

- navigation locators
- pagination logic
- `app/constants.py`

### <ins> Data Extraction Tests (asynchronous) </ins>

```bash
uv sync # pytest-asyncio
uv run pytest tests/e2e/async -v -s
```

**Important flags:**

- `-v` → verbose testing
- `-s` → disable capture (show stdout even for PASSED test)

**Debugging:**

- set `headless=False` to show UI
- uncomment `print(json.dumps(record, ensure_ascii=False, indent=2))` to display record in `.json` format

**Target:**

- `_extract_*_data` methods

## About

Refer to [/docs](https://github.com/smart-study-inc/fukunavi-crawler/tree/main/docs) for more information.
