def partition(values: list, worker_count: int) -> list[list]:
    """
    Split values across workers in round-robin order.

    Example:
    - values = [1, 2, 3, 4, 5, 6]
    - worker_count = 2

    worker0
    - → [1, 3, 5]

    worker1
    - → [2, 4, 6]
    """

    partitions: list[list] = []

    for _ in range(worker_count):
        partitions.append([])

    for i, value in enumerate(values):
        worker_id = i % worker_count
        partitions[worker_id].append(value)

    return partitions
