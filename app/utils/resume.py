from collections.abc import Iterable
from typing import Any


class ResumeManager:
    """
    Manages saved crawl position so interrupted crawls can continue safely.
    """

    def __init__(self, saved_position: dict | None):
        self._pending_resume_position: dict = (
            saved_position.copy() if saved_position else {}
        )

        # Indicates whether resume logic is currently active.
        self._is_resuming: bool = bool(saved_position)

    def is_resuming(self) -> bool:
        """
        Checks if saved-position filtering should be applied.
        """

        return self._is_resuming

    def stop_resuming(self) -> None:
        """
        Stops resume logic once the saved position has been passed.
        """

        self._is_resuming = False
        self._pending_resume_position.clear()

    def clear_key(self, key: str) -> None:
        """
        Removes a single key from the pending resume position.
        Stops resume logic if no more keys remain.
        """

        self._pending_resume_position.pop(key, None)
        if not self._pending_resume_position:
            self.stop_resuming()

    def get_saved_value(self, checkpoint_key: str) -> Any | None:
        """
        Returns the saved checkpoint value for the given key.
        """

        return self._pending_resume_position.get(checkpoint_key)

    def continue_from_checkpoint(self, checkpoint_key: str, all_values: Iterable[Any]):
        """
        Skips values that were already processed before the saved position.
        """

        # CASE 1: No resume active OR this position key is not in the saved checkpoint.
        # Pass through all values unchanged.
        if not self._is_resuming or checkpoint_key not in self._pending_resume_position:
            for value in all_values:
                yield value
            return

        # CASE 2: Resume active for this position key.
        # Skip values until the saved value, then yield from there onward.
        saved_value = self._pending_resume_position[checkpoint_key]
        has_reached_saved_value = False

        for value in all_values:
            # PHASE 1: Before saved position - skip already processed values.
            if not has_reached_saved_value:
                if value == saved_value:
                    has_reached_saved_value = True
                    yield value
                else:
                    continue

            # PHASE 2: At or after saved position - yield remaining values.
            else:
                yield value

        # Cleanup: this position key has finished resume handling.
        self._pending_resume_position.pop(checkpoint_key, None)

        # If no more saved position keys remain, stop resume logic.
        if not self._pending_resume_position:
            self.stop_resuming()
