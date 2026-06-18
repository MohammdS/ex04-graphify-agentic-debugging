"""Rate-limit configuration loading and queue-status reporting types."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class QueueFullError(RuntimeError):
    """Raised when ``execute`` is called while the queue is at max depth."""


@dataclass(frozen=True)
class ServiceLimits:
    requests_per_minute: int
    requests_per_hour: int
    concurrent_max: int
    retry_after_seconds: float
    max_retries: int
    max_queue_depth: int


@dataclass(frozen=True)
class RateLimitConfig:
    version: str
    services: dict[str, ServiceLimits]

    @classmethod
    def from_file(cls, path: str | Path) -> "RateLimitConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        services = {
            name: ServiceLimits(**block) for name, block in data["services"].items()
        }
        return cls(version=data.get("version", "1.0"), services=services)

    def for_service(self, service: str = "default") -> ServiceLimits:
        try:
            return self.services[service]
        except KeyError as exc:
            raise KeyError(
                f"No rate-limit config for service '{service}'; "
                f"available: {sorted(self.services)}"
            ) from exc


@dataclass
class QueueStatus:
    depth: int
    max_depth: int
    in_flight: int
    total_executed: int
    total_queued: int
    total_rejected: int
    total_retries: int
