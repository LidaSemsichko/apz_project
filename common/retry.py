import asyncio
import time
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def retry(
    operation: Callable[[], T],
    *,
    attempts: int = 15,
    delay_seconds: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    last_error: BaseException | None = None

    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except exceptions as error:
            last_error = error
            if on_retry:
                on_retry(attempt, error)
            if attempt < attempts:
                time.sleep(delay_seconds)

    raise last_error or RuntimeError("Retry operation failed")


async def async_retry(
    operation: Callable[[], T],
    *,
    attempts: int = 15,
    delay_seconds: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    last_error: BaseException | None = None

    for attempt in range(1, attempts + 1):
        try:
            result = operation()
            if asyncio.iscoroutine(result):
                return await result
            return result
        except exceptions as error:
            last_error = error
            if on_retry:
                on_retry(attempt, error)
            if attempt < attempts:
                await asyncio.sleep(delay_seconds)

    raise last_error or RuntimeError("Retry operation failed")
