"""Centralized API call manager: rate limiting, queueing, retries, and logging.

All outbound calls to a rate-limited external API (the LLM endpoints used by
``llm_support.call_llm`` and ``compare_token_usage.call_model``) must go
through :class:`ApiGatekeeper.execute` instead of being invoked directly, so
that rate limits, backpressure, retries, and call logging are enforced in one
place. Limits are always loaded from ``config/rate_limits.json``, never
hardcoded.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Any, Callable

from rate_limit_config import QueueFullError, QueueStatus, RateLimitConfig, ServiceLimits

logger = logging.getLogger(__name__)


class ApiGatekeeper:
    """Centralized API call manager."""

    def __init__(
        self,
        config: RateLimitConfig,
        service: str = "default",
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._limits = config.for_service(service)
        self._service = service
        self._clock = clock
        self._sleep = sleep

        self._lock = threading.Lock()
        self._minute_window: deque[float] = deque()
        self._hour_window: deque[float] = deque()
        self._queue_depth = 0
        self._in_flight = 0
        self._total_executed = 0
        self._total_queued = 0
        self._total_rejected = 0
        self._total_retries = 0

    def execute(self, api_call: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute ``api_call(*args, **kwargs)`` through rate limiting, queueing,
        and retries. Logs every attempt, queue, backpressure, and drain event."""
        self._enter_queue_or_raise()
        try:
            self._wait_for_capacity()
            try:
                return self._call_with_retry(api_call, args, kwargs)
            finally:
                with self._lock:
                    self._in_flight -= 1
        finally:
            self._leave_queue()

    def get_queue_status(self) -> QueueStatus:
        """Return queue depth and stats."""
        with self._lock:
            return QueueStatus(
                depth=self._queue_depth,
                max_depth=self._limits.max_queue_depth,
                in_flight=self._in_flight,
                total_executed=self._total_executed,
                total_queued=self._total_queued,
                total_rejected=self._total_rejected,
                total_retries=self._total_retries,
            )

    # -- internals ------------------------------------------------------

    def _enter_queue_or_raise(self) -> None:
        with self._lock:
            if self._queue_depth >= self._limits.max_queue_depth:
                self._total_rejected += 1
                logger.warning(
                    "gatekeeper backpressure: queue full (depth=%s/%s) for service=%s, rejecting call",
                    self._queue_depth,
                    self._limits.max_queue_depth,
                    self._service,
                )
                raise QueueFullError(
                    f"Gatekeeper queue full ({self._queue_depth}/{self._limits.max_queue_depth}) "
                    f"for service '{self._service}'"
                )
            self._queue_depth += 1
            self._total_queued += 1
            logger.debug("gatekeeper enqueue: service=%s depth=%s", self._service, self._queue_depth)

    def _leave_queue(self) -> None:
        with self._lock:
            self._queue_depth -= 1
            if self._queue_depth == 0:
                logger.debug("gatekeeper drain: queue empty for service=%s", self._service)

    def _evict_expired(self, now: float) -> None:
        while self._minute_window and now - self._minute_window[0] >= 60:
            self._minute_window.popleft()
        while self._hour_window and now - self._hour_window[0] >= 3600:
            self._hour_window.popleft()

    def _next_available_in(self, now: float) -> float:
        candidates = []
        if len(self._minute_window) >= self._limits.requests_per_minute and self._minute_window:
            candidates.append(60 - (now - self._minute_window[0]))
        if len(self._hour_window) >= self._limits.requests_per_hour and self._hour_window:
            candidates.append(3600 - (now - self._hour_window[0]))
        if not candidates:
            candidates.append(0.05)  # concurrency-only contention: short poll backoff
        return max(0.01, min(candidates))

    def _wait_for_capacity(self) -> None:
        while True:
            with self._lock:
                now = self._clock()
                self._evict_expired(now)
                under_minute = len(self._minute_window) < self._limits.requests_per_minute
                under_hour = len(self._hour_window) < self._limits.requests_per_hour
                under_concurrency = self._in_flight < self._limits.concurrent_max
                if under_minute and under_hour and under_concurrency:
                    self._minute_window.append(now)
                    self._hour_window.append(now)
                    self._in_flight += 1
                    return
                wait_for = self._next_available_in(now)
            logger.info(
                "gatekeeper rate-limited: service=%s, waiting %.2fs", self._service, wait_for
            )
            self._sleep(wait_for)

    def _call_with_retry(
        self, api_call: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> Any:
        attempt = 0
        while True:
            attempt += 1
            try:
                logger.info(
                    "gatekeeper executing call: service=%s attempt=%s/%s",
                    self._service,
                    attempt,
                    self._limits.max_retries,
                )
                result = api_call(*args, **kwargs)
            except Exception:
                if attempt > self._limits.max_retries:
                    logger.error(
                        "gatekeeper call failed permanently: service=%s after %s attempts",
                        self._service,
                        attempt,
                        exc_info=True,
                    )
                    raise
                with self._lock:
                    self._total_retries += 1
                logger.warning(
                    "gatekeeper retrying call: service=%s attempt=%s/%s, waiting %.2fs",
                    self._service,
                    attempt,
                    self._limits.max_retries,
                    self._limits.retry_after_seconds,
                    exc_info=True,
                )
                self._sleep(self._limits.retry_after_seconds)
                continue
            with self._lock:
                self._total_executed += 1
            logger.info("gatekeeper call succeeded: service=%s", self._service)
            return result
