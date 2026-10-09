import os

from dotenv import load_dotenv

from app.utils.gcs_storage import GCSStorage

load_dotenv()

# This controls how long the crawler waits for selectors, navigation, etc.
# Default: 25 seconds (25000 milliseconds).
CRAWLER_TIMEOUT_MS = int(os.getenv("CRAWLER_TIMEOUT_MS", "25000"))

# This is the maximum runtime for the crawler.
# Default: 8 hours (28800 seconds).
MAX_RUNTIME_SECONDS = int(os.getenv("MAX_RUNTIME_SECONDS", "28800"))

# GCS bucket name used by the crawler.
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
if not GCS_BUCKET_NAME:
    raise ValueError("GCS_BUCKET_NAME is required")

GCS_STORAGE = GCSStorage(GCS_BUCKET_NAME)

# This is the number of concurrent workers for the crawler.
# Default: 3 workers.
WORKER_COUNT = int(os.getenv("WORKER_COUNT", "3"))
