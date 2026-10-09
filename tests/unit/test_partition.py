from app.utils.partition import partition


def test_partition_distributes_values_round_robin():
    """Verify that values are distributed in round-robin."""
    values = [1, 2, 3, 4, 5, 6]
    workers = 2

    result = partition(values, workers)

    assert result == [[1, 3, 5], [2, 4, 6]]


def test_partition_with_three_workers():
    """Verify distribution with three workers."""
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    workers = 3

    result = partition(values, workers)

    assert result == [[1, 4, 7], [2, 5, 8], [3, 6, 9]]


def test_partition_with_uneven_distribution():
    """Verify behavior when values don't divide evenly across workers."""
    values = [1, 2, 3, 4, 5]
    workers = 2

    result = partition(values, workers)

    # Worker 0 gets 3 items, Worker 1 gets 2 items
    assert result == [[1, 3, 5], [2, 4]]


def test_partition_with_single_worker():
    """Verify that single worker gets all values."""
    values = [1, 2, 3, 4, 5]
    workers = 1

    result = partition(values, workers)

    assert result == [[1, 2, 3, 4, 5]]


def test_partition_with_more_workers_than_values():
    """Verify behavior when there are more workers than values."""
    values = [1, 2, 3]
    workers = 5

    result = partition(values, workers)

    # First 3 workers get 1 value each, last 2 workers get empty lists
    assert result == [[1], [2], [3], [], []]


def test_partition_with_empty_list():
    """Verify behavior with empty input list."""
    values = []
    workers = 3

    result = partition(values, workers)

    assert result == [[], [], []]


def test_partition_preserves_order_within_partitions():
    """Verify that order is preserved within each partition."""
    values = ["a", "b", "c", "d", "e", "f", "g"]
    workers = 3

    result = partition(values, workers)

    assert result == [["a", "d", "g"], ["b", "e"], ["c", "f"]]


def test_partition_returns_correct_number_of_partitions():
    """Verify that the number of partitions matches the number of workers."""
    values = [1, 2, 3, 4, 5]
    workers = 4

    result = partition(values, workers)

    assert len(result) == workers


def test_partition_with_realistic_area_codes():
    """Verify distribution with actual production area codes."""
    # Actual area codes from corporations_crawler.py
    area_codes = [
        "0",
        "1",
        "2",
        "13361",
        "13362",
        "13363",
        "13364",
        "13381",
        "13382",
        "13401",
        "13402",
        "13421",
    ]
    workers = 3  # WORKER_COUNT in production

    result = partition(area_codes, workers)

    # Verify round-robin distribution across 3 workers
    assert result == [
        ["0", "13361", "13364", "13401"],  # Worker 0: indices 0, 3, 6, 9
        ["1", "13362", "13381", "13402"],  # Worker 1: indices 1, 4, 7, 10
        ["2", "13363", "13382", "13421"],  # Worker 2: indices 2, 5, 8, 11
    ]
    assert len(result) == workers
    # Verify all area codes are distributed
    assert set(result[0] + result[1] + result[2]) == set(area_codes)
