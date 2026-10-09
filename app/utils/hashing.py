import hashlib
import json


def generate_data_hash(record: dict) -> str:
    """
    Generates a SHA256 hash for a given record, excluding certain fields.
    """

    clean = {
        k: v
        for k, v in record.items()
        if k not in {"created_at", "updated_at", "data_hash", "source_url"}
    }

    serialized = json.dumps(clean, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
