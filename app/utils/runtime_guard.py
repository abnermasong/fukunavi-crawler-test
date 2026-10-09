import time


class RuntimeLimitReachedException(Exception):
    """
    Exception raised when the runtime limit is reached.
    """


class RuntimeGuardManager:
    """
    Manages a runtime limit for workers, allowing them to check if they should stop processing.
    """

    def __init__(self, runtime_limit_seconds: int):
        self.deadline = time.time() + runtime_limit_seconds

    def check(self) -> None:
        """
        Checks if the runtime limit has been exceeded and raises an exception if so.
        """

        current_time = time.time()

        if current_time >= self.deadline:
            raise RuntimeLimitReachedException()
