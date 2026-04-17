from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    timestamp: datetime
    pool_size: int
    checked_out: int
    overflow: int
    checked_in: int
    avg_cmd_latency: float | None
    max_cmd_latency: float | None
    memory_usage_mb: float
    seconds_since_snapshot: float
    is_stale: bool


class LatencyWindow(BaseModel):
    hours: int
    avg_ms: float | None
    max_ms: float | None


class PerformanceResponse(BaseModel):
    windows: list[LatencyWindow]
