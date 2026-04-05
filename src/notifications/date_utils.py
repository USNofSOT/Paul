from __future__ import annotations

from datetime import UTC, date, datetime


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def to_local_date(value: datetime) -> date:
    return ensure_utc(value).date()


def local_today(now: datetime | None = None) -> date:
    resolved_now = ensure_utc(now or datetime.now(UTC))
    return resolved_now.date()
