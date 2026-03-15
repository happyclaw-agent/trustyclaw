"""Async retry helpers for transient network operations."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_with_exponential_backoff(
    operation: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 3,
    base_delay_seconds: float = 0.2,
    max_delay_seconds: float = 2.0,
    jitter_seconds: float = 0.0,
    is_retryable: Callable[[Exception], bool] | None = None,
) -> T:
    """
    Execute an async operation with bounded exponential backoff retries.

    Args:
        operation: Async callable to execute.
        max_retries: Number of retries after the first failed attempt.
        base_delay_seconds: Initial delay before retrying.
        max_delay_seconds: Upper bound for backoff delay.
        jitter_seconds: Optional additive random jitter in seconds.
        is_retryable: Optional predicate to decide retry eligibility.

    Returns:
        The operation result.

    Raises:
        The last exception raised by ``operation`` when retries are exhausted
        or when the exception is not retryable.
    """
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")
    if base_delay_seconds < 0 or max_delay_seconds < 0 or jitter_seconds < 0:
        raise ValueError("delay and jitter settings must be >= 0")

    should_retry = is_retryable or (lambda exc: True)

    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except Exception as exc:
            if attempt >= max_retries or not should_retry(exc):
                raise

            delay = min(max_delay_seconds, base_delay_seconds * (2**attempt))
            if jitter_seconds:
                delay += random.uniform(0.0, jitter_seconds)
            await asyncio.sleep(delay)

    raise RuntimeError("unreachable")
