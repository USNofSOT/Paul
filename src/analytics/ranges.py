from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

RANGE_OPTIONS = {
    "1h": timedelta(hours=1),
    "3h": timedelta(hours=3),
    "6h": timedelta(hours=6),
    "12h": timedelta(hours=12),
    "1d": timedelta(days=1),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "365d": timedelta(days=365),
    "730d": timedelta(days=730),
    "1825d": timedelta(days=1825),
}

ROLE_SIZE_RANGE_LABELS = {"1h": "1d", "3h": "1d", "6h": "1d", "12h": "1d"}
ANALYTICS_RANGE_OPTIONS = (
    "1h",
    "1d",
    "7d",
    "30d",
    "90d",
    "365d",
    "730d",
    "1825d",
    "all",
)
SHIP_ANALYTICS_RANGE_OPTIONS = (
    "1d",
    "7d",
    "30d",
    "90d",
    "365d",
    "730d",
    "1825d",
    "all",
)
SHIP_HISTORY_RANGE_OPTIONS = (
    "7d",
    "30d",
    "90d",
    "365d",
    "730d",
    "1825d",
    "all",
)
ROLE_SIZE_ANALYTICS_RANGE_OPTIONS = (
    "1d",
    "7d",
    "30d",
    "90d",
    "365d",
    "730d",
    "1825d",
    "all",
)


@dataclass(frozen=True)
class TimeRange:
    label: str
    start: datetime | None
    end: datetime
    bucket: str
    buckets: tuple[datetime, ...]

    @classmethod
    def from_reference(cls, label: str, reference_time: datetime) -> TimeRange:
        return resolve_time_range(label, reference_time)


def resolve_time_range(label: str, reference_time: datetime | None = None) -> TimeRange:
    reference = (reference_time or datetime.utcnow()).replace(microsecond=0)
    normalized_label = (label or "30d").lower()
    if normalized_label == "all":
        bucket = bucket_for_range(normalized_label)
        return TimeRange(
            label=normalized_label,
            start=None,
            end=reference,
            bucket=bucket,
            buckets=(bucket_start_for(reference, bucket),),
        )
    if normalized_label not in RANGE_OPTIONS:
        normalized_label = "30d"
    start = reference - RANGE_OPTIONS[normalized_label]
    bucket = bucket_for_range(normalized_label)
    return TimeRange(
        label=normalized_label,
        start=start,
        end=reference,
        bucket=bucket,
        buckets=tuple(generate_buckets(start, reference, bucket)),
    )


def role_size_time_range(
        label: str,
        reference_time: datetime | None = None,
) -> TimeRange:
    reference = (reference_time or datetime.utcnow()).replace(microsecond=0)
    normalized_label = (label or "30d").lower()
    normalized_label = ROLE_SIZE_RANGE_LABELS.get(normalized_label, normalized_label)
    if normalized_label == "all":
        bucket = role_size_bucket_for_range(normalized_label)
        return TimeRange(
            label=normalized_label,
            start=None,
            end=reference,
            bucket=bucket,
            buckets=(bucket_start_for(reference, bucket),),
        )
    if normalized_label not in RANGE_OPTIONS:
        normalized_label = "30d"
    bucket = role_size_bucket_for_range(normalized_label)
    start = reference - RANGE_OPTIONS[normalized_label]
    return TimeRange(
        label=normalized_label,
        start=start,
        end=reference,
        bucket=bucket,
        buckets=tuple(generate_buckets(start, reference, bucket)),
    )


def role_size_bucket_for_range(label: str) -> str:
    if label in {"1d", "7d", "30d"}:
        return "day"
    if label == "90d":
        return "week"
    return "month"


def bucket_for_range(label: str) -> str:
    if label in {"1h", "3h"}:
        return "5min"
    if label in {"6h", "12h", "1d"}:
        return "hour"
    if label == "7d":
        return "6hour"
    if label == "30d":
        return "day"
    if label == "90d":
        return "week"
    return "month"


def buckets_for_observed_range(
        time_range: TimeRange,
        values: Iterable[datetime | None],
) -> tuple[datetime, ...]:
    if time_range.start is not None:
        return time_range.buckets
    observed = [
        value for value in values if value is not None and value <= time_range.end
    ]
    start = min(observed) if observed else time_range.end
    return tuple(generate_buckets(start, time_range.end, time_range.bucket))


def generate_buckets(start: datetime, end: datetime, bucket: str) -> list[datetime]:
    current = bucket_start_for(start, bucket)
    final = bucket_start_for(end, bucket)
    buckets: list[datetime] = []
    while current <= final:
        buckets.append(current)
        current = next_bucket_start(current, bucket)
    return buckets


def bucket_start_for(value: datetime, bucket: str) -> datetime:
    if bucket == "5min":
        minute = value.minute - (value.minute % 5)
        return value.replace(minute=minute, second=0, microsecond=0)
    if bucket == "hour":
        return value.replace(minute=0, second=0, microsecond=0)
    if bucket == "6hour":
        hour = value.hour - (value.hour % 6)
        return value.replace(hour=hour, minute=0, second=0, microsecond=0)
    if bucket == "day":
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    if bucket == "week":
        day = value.replace(hour=0, minute=0, second=0, microsecond=0)
        return day - timedelta(days=day.weekday())
    if bucket == "month":
        return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unknown analytics bucket: {bucket}")


def next_bucket_start(value: datetime, bucket: str) -> datetime:
    if bucket == "5min":
        return value + timedelta(minutes=5)
    if bucket == "hour":
        return value + timedelta(hours=1)
    if bucket == "6hour":
        return value + timedelta(hours=6)
    if bucket == "day":
        return value + timedelta(days=1)
    if bucket == "week":
        return value + timedelta(weeks=1)
    if bucket == "month":
        if value.month == 12:
            return value.replace(year=value.year + 1, month=1)
        return value.replace(month=value.month + 1)
    raise ValueError(f"Unknown analytics bucket: {bucket}")


def bucket_label(value: datetime, bucket: str) -> str:
    if bucket in {"5min", "hour", "6hour"}:
        return value.strftime("%d %b %H:%M")
    if bucket in {"day", "week"}:
        return value.strftime("%d %b")
    if bucket == "month":
        return value.strftime("%b %Y")
    return value.isoformat()
