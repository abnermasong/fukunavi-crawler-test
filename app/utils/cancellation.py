import threading


class GracefulShutdownRequestedException(Exception):
    """Raised when cooperative cancellation is requested."""


class CancellationFlagManager:
    """
    Thread-safe flag for cooperative cancellation between workers.

    When one worker encounters an error, it sets this flag to signal
    other workers to exit gracefully at their next safe boundary.
    """

    def __init__(self) -> None:
        self._flag = threading.Event()

    def request_shutdown(self) -> None:
        """
        Signal all workers to exit gracefully.
        """

        self._flag.set()

    def check(self) -> None:
        """
        Raise an exception if graceful shutdown has been requested.
        """

        if self._flag.is_set():
            raise GracefulShutdownRequestedException()
