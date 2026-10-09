import json
from pathlib import Path


def start_ndjson_file(filename: str) -> Path:
    """
    Create or truncate an NDJSON file and return its Path object.

    This ensures we start with a clean file for each crawl, and we can append to it
    """

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    file_path = output_dir / filename
    file_path.open("w", encoding="utf-8").close()
    return file_path


def append_ndjson(record: dict, filename: str) -> None:
    """
    Appends a single record to an NDJSON file.

    This ensures each record is written immediately, reducing data loss risk in case of a crash.
    """

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    file_path = output_dir / filename

    with file_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
