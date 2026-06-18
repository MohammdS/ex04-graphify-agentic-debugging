"""Offline unit tests for the centralized ApiGatekeeper.

These never sleep for real: rate-limit window and retry-backoff behavior is
exercised with an injected fake clock/sleep pair so the suite stays fast and
deterministic.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))

import gatekeeper  # noqa: E402


# --- fake clock/sleep helpers -------------------------------------------------

class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class RecordingSleep:
    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)
        self.clock.advance(seconds)


def make_config(**overrides) -> gatekeeper.RateLimitConfig:
    defaults = dict(
        requests_per_minute=30,
        requests_per_hour=500,
        concurrent_max=5,
        retry_after_seconds=30,
        max_retries=3,
        max_queue_depth=50,
    )
    defaults.update(overrides)
    return gatekeeper.RateLimitConfig(
        version="1.00", services={"default": gatekeeper.ServiceLimits(**defaults)}
    )


# --- config loading -------------------------------------------------------

def test_real_config_file_loads():
    config = gatekeeper.RateLimitConfig.from_file(ROOT / "config" / "rate_limits.json")
    limits = config.for_service("default")
    assert limits.requests_per_minute == 30
    assert limits.requests_per_hour == 500
    assert limits.concurrent_max == 5
    assert limits.retry_after_seconds == 30
    assert limits.max_retries == 3
    assert limits.max_queue_depth == 50


def test_for_service_missing_raises():
    config = make_config()
    with pytest.raises(KeyError):
        config.for_service("nonexistent")


# --- successful passthrough ------------------------------------------------

def test_execute_passthrough_returns_value():
    gk = gatekeeper.ApiGatekeeper(make_config(), clock=FakeClock(), sleep=lambda s: None)
    assert gk.execute(lambda x: x * 2, 21) == 42
    status = gk.get_queue_status()
    assert status.total_executed == 1
    assert status.depth == 0
    assert status.in_flight == 0


def test_execute_passes_args_and_kwargs():
    gk = gatekeeper.ApiGatekeeper(make_config(), clock=FakeClock(), sleep=lambda s: None)

    def add(a, b, c=0):
        return a + b + c

    assert gk.execute(add, 1, 2, c=3) == 6


# --- rate-limit window gating ----------------------------------------------

def test_rate_limit_blocks_until_window_clears():
    clock = FakeClock()
    sleep = RecordingSleep(clock)
    gk = gatekeeper.ApiGatekeeper(
        make_config(requests_per_minute=2, concurrent_max=10), clock=clock, sleep=sleep
    )
    gk.execute(lambda: "ok")
    gk.execute(lambda: "ok")
    gk.execute(lambda: "ok")  # 3rd call exceeds the per-minute window
    assert sleep.calls, "expected gatekeeper to sleep while rate-limited"
    assert gk.get_queue_status().total_executed == 3


def test_rate_limit_window_clears_after_evicting_old_calls():
    clock = FakeClock()
    sleep = RecordingSleep(clock)
    gk = gatekeeper.ApiGatekeeper(
        make_config(requests_per_minute=1, concurrent_max=10), clock=clock, sleep=sleep
    )
    gk.execute(lambda: "ok")
    clock.advance(61)  # window fully expires without needing to sleep
    gk.execute(lambda: "ok")
    assert not sleep.calls


# --- retry behavior ----------------------------------------------------------

def test_retry_then_succeed():
    clock = FakeClock()
    sleep = RecordingSleep(clock)
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise ConnectionError("transient")
        return "ok"

    gk = gatekeeper.ApiGatekeeper(make_config(max_retries=3), clock=clock, sleep=sleep)
    assert gk.execute(flaky) == "ok"
    assert attempts["n"] == 2
    assert gk.get_queue_status().total_retries == 1
    assert sleep.calls == [30]


def test_retry_exhausted_raises_original_exception():
    clock = FakeClock()
    sleep = RecordingSleep(clock)

    def always_fails():
        raise ConnectionError("permanent")

    gk = gatekeeper.ApiGatekeeper(make_config(max_retries=2), clock=clock, sleep=sleep)
    with pytest.raises(ConnectionError, match="permanent"):
        gk.execute(always_fails)
    assert gk.get_queue_status().total_retries == 2


# --- queue backpressure --------------------------------------------------------

def test_queue_full_raises_queue_full_error():
    gk = gatekeeper.ApiGatekeeper(
        make_config(max_queue_depth=0), clock=FakeClock(), sleep=lambda s: None
    )
    with pytest.raises(gatekeeper.QueueFullError):
        gk.execute(lambda: "unreachable")
    status = gk.get_queue_status()
    assert status.total_rejected == 1
    assert status.total_executed == 0


def test_queue_status_reports_max_depth():
    gk = gatekeeper.ApiGatekeeper(
        make_config(max_queue_depth=7), clock=FakeClock(), sleep=lambda s: None
    )
    assert gk.get_queue_status().max_depth == 7


# --- logging ------------------------------------------------------------------

def test_logging_emits_backpressure_warning(caplog):
    gk = gatekeeper.ApiGatekeeper(
        make_config(max_queue_depth=0), clock=FakeClock(), sleep=lambda s: None
    )
    with caplog.at_level(logging.WARNING, logger="gatekeeper"):
        with pytest.raises(gatekeeper.QueueFullError):
            gk.execute(lambda: "x")
    assert any("backpressure" in r.message for r in caplog.records)


def test_logging_emits_retry_warning(caplog):
    clock = FakeClock()
    sleep = RecordingSleep(clock)
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("boom")
        return "ok"

    gk = gatekeeper.ApiGatekeeper(make_config(), clock=clock, sleep=sleep)
    with caplog.at_level(logging.WARNING, logger="gatekeeper"):
        gk.execute(flaky)
    assert any("retrying" in r.message for r in caplog.records)


def test_logging_emits_success_info(caplog):
    gk = gatekeeper.ApiGatekeeper(make_config(), clock=FakeClock(), sleep=lambda s: None)
    with caplog.at_level(logging.INFO, logger="gatekeeper"):
        gk.execute(lambda: "ok")
    assert any("succeeded" in r.message for r in caplog.records)
