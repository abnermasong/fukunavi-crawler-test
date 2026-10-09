import asyncio
import random
import time
from collections.abc import Awaitable, Callable

from app.utils.runtime_guard import RuntimeGuardManager


async def retry_async(
    func: Callable[[], Awaitable],
    *,
    retries: int = 3,
    base_delay: float = 2.0,
    backoff_factor: float = 2.0,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
    runtime_guard: RuntimeGuardManager | None = None,
    worker_id: int | None = None,
):
    """
    Retry an async function with exponential backoff and jitter.

    delay = base_delay * (backoff_factor ** attempt) + jitter
    """

    for attempt in range(retries + 1):
        if runtime_guard:
            runtime_guard.check()

        try:
            return await func()

        except retry_exceptions as e:
            if attempt == retries:
                raise

            if runtime_guard:
                runtime_guard.check()

            delay = base_delay * (backoff_factor**attempt)
            jitter = random.uniform(0, 1)
            sleep_time = delay + jitter

            print(
                f"[{__name__}] [Worker #{worker_id}] Attempt {attempt + 1}/{retries} failed: {e}."
                f"Retrying in {sleep_time:.2f}s"
            )

            start = time.time()
            while time.time() - start < sleep_time:
                if runtime_guard:
                    runtime_guard.check()
                await asyncio.sleep(0.5)  # Sleep in small increments to check guard
