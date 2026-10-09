from app.utils.hashing import generate_data_hash


def test_generate_data_hash_returns_sha256_hex(corporation_record):
    """Verify that the function returns a valid SHA256 hash (64 hex characters)."""
    hash_result = generate_data_hash(corporation_record)

    # SHA256 hex string should be exactly 64 characters
    assert len(hash_result) == 64
    # Should only contain hexadecimal characters
    assert all(c in "0123456789abcdef" for c in hash_result)


def test_generate_data_hash_ignores_created_at(corporation_record):
    """Verify that created_at field does not affect generating data_hash."""
    base_record = corporation_record.copy()

    modified_record = base_record.copy()
    modified_record["created_at"] = "2026-04-15T10:00:00.000000+00:00"

    assert generate_data_hash(base_record) == generate_data_hash(modified_record)


def test_generate_data_hash_ignores_updated_at(corporation_record):
    """Verify that updated_at field does not affect generating data_hash."""
    base_record = corporation_record.copy()
    base_record["updated_at"] = "2026-03-03T07:54:45.447545+00:00"

    modified_record = base_record.copy()
    modified_record["updated_at"] = "2026-04-15T10:00:00.000000+00:00"

    assert generate_data_hash(base_record) == generate_data_hash(modified_record)


def test_generate_data_hash_ignores_source_url(corporation_record):
    """Verify that source_url field does not affect generating data_hash."""
    base_record = corporation_record.copy()

    modified_record = base_record.copy()
    modified_record["source_url"] = "https://example.com/different"

    assert generate_data_hash(base_record) == generate_data_hash(modified_record)


def test_generate_data_hash_ignores_data_hash(corporation_record):
    """Verify that data_hash field does not affect generating data_hash."""
    base_record = corporation_record.copy()

    modified_record = base_record.copy()
    modified_record["data_hash"] = "completely_different_hash_value"

    assert generate_data_hash(base_record) == generate_data_hash(modified_record)


def test_generate_data_hash_changes_on_data_changes(corporation_record):
    """Verify that the data_hash changes when corporation data changes."""
    base_record = corporation_record.copy()

    # Change a corporation field (not an excluded field)
    modified_record = base_record.copy()
    modified_record["address"] = "123-4567   New Address, Tokyo"

    assert generate_data_hash(base_record) != generate_data_hash(modified_record)


def test_generate_data_hash_is_stable_for_same_corporation_data_with_different_key_order(
    corporation_record,
):
    """Verify that data_hash is consistent regardless of key order."""
    base = corporation_record

    # Same data, different key order
    record1 = {
        "corporation_name": base["corporation_name"],
        "corporation_type": base["corporation_type"],
        "address": base["address"],
        "phone_number": base["phone_number"],
        "update_date": base["update_date"],
    }

    record2 = {
        "update_date": base["update_date"],
        "phone_number": base["phone_number"],
        "address": base["address"],
        "corporation_type": base["corporation_type"],
        "corporation_name": base["corporation_name"],
    }

    assert generate_data_hash(record1) == generate_data_hash(record2)
