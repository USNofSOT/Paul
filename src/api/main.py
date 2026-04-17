from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api import cache
from src.api.schemas import HealthResponse, LatencyWindow, PerformanceResponse
from src.data.repository.health_snapshot_repository import HealthSnapshotRepository

log = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(docs_url=None, redoc_url=None, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health", response_model=HealthResponse)
@limiter.limit("6/minute")
def health(request: Request):
    cached = cache.get("health")
    if cached is not None:
        return cached

    repo = HealthSnapshotRepository()
    try:
        row = repo.get_latest()
    finally:
        repo.close_session()

    if row is None:
        raise HTTPException(status_code=503, detail="No health data available yet")

    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    seconds_since = (now - row.timestamp).total_seconds()
    response = HealthResponse(
        timestamp=row.timestamp,
        pool_size=row.pool_size,
        checked_out=row.checked_out,
        overflow=row.overflow,
        checked_in=row.checked_in,
        avg_cmd_latency=row.avg_cmd_latency,
        max_cmd_latency=row.max_cmd_latency,
        memory_usage_mb=row.memory_usage_mb,
        seconds_since_snapshot=seconds_since,
        is_stale=seconds_since > 600,
    )
    cache.set("health", response, ttl=30)
    return response


@app.get("/performance", response_model=PerformanceResponse)
@limiter.limit("6/minute")
def performance(request: Request):
    cached = cache.get("performance")
    if cached is not None:
        return cached

    windows = []
    repo = HealthSnapshotRepository()
    try:
        for hours in [1, 3, 6, 12, 24]:
            avg_ms, max_ms = repo.get_avg_max_latency(hours)
            windows.append(
                LatencyWindow(
                    hours=hours,
                    avg_ms=avg_ms,
                    max_ms=max_ms,
                )
            )
    finally:
        repo.close_session()

    response = PerformanceResponse(windows=windows)
    cache.set("performance", response, ttl=60)
    return response


@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("5/minute")
async def catch_all(request: Request, path_name: str):
    raise HTTPException(status_code=404, detail="Not Found")
