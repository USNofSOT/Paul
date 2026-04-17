from __future__ import annotations

import time
from typing import Any

_store: dict[str, tuple[Any, float]] = {}


def get(key: str) -> Any | None:
    entry = _store.get(key)
    if entry is None:
        return None
    data, expires_at = entry
    if time.monotonic() > expires_at:
        del _store[key]
        return None
    return data


def set(key: str, data: Any, ttl: int) -> None:
    _store[key] = (data, time.monotonic() + ttl)
