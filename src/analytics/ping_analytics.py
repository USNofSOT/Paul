from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from src.analytics.ranges import (
    TimeRange,
    bucket_start_for,
    buckets_for_observed_range,
)
from src.data.models import RolePingLog


@dataclass(frozen=True)
class PingAnalyticsFilters:
    time_range: TimeRange
    ping_role_id: int | None = None
    ping_type: str | None = None
    ship_role_id: int | None = None
    user_id: int | None = None
    has_vp_permission: bool | None = None


@dataclass(frozen=True)
class PingBucket:
    start: datetime
    total: int = 0
    vp_enabled: int = 0
    non_vp: int = 0


@dataclass(frozen=True)
class PingAnalyticsSummary:
    filters: PingAnalyticsFilters
    total_pings: int
    vp_enabled_pings: int
    non_vp_pings: int
    deleted_rows_excluded: int
    rank_counts: dict[int, int]
    ship_counts: dict[int, int]
    user_counts: list[tuple[int, int]]
    bucket_series: list[PingBucket]


class PingAnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def build_summary(
            self,
            filters: PingAnalyticsFilters,
            *,
            limit: int = 10,
    ) -> PingAnalyticsSummary:
        active_rows = self._query(filters, include_deleted=False).all()
        deleted_rows_excluded = self._query(filters, include_deleted=True).filter(
            RolePingLog.is_deleted.is_(True)
        ).count()

        bucket_total: dict[datetime, int] = defaultdict(int)
        bucket_vp: dict[datetime, int] = defaultdict(int)
        bucket_non_vp: dict[datetime, int] = defaultdict(int)
        for row in active_rows:
            bucket = bucket_start_for(row.created_at, filters.time_range.bucket)
            bucket_total[bucket] += 1
            if row.has_vp_permission:
                bucket_vp[bucket] += 1
            else:
                bucket_non_vp[bucket] += 1

        buckets = buckets_for_observed_range(
            filters.time_range,
            [row.created_at for row in active_rows],
        )

        return PingAnalyticsSummary(
            filters=filters,
            total_pings=len(active_rows),
            vp_enabled_pings=sum(1 for row in active_rows if row.has_vp_permission),
            non_vp_pings=sum(1 for row in active_rows if not row.has_vp_permission),
            deleted_rows_excluded=deleted_rows_excluded,
            rank_counts=dict(
                Counter(
                    row.highest_rank_role_id
                    for row in active_rows
                    if row.highest_rank_role_id is not None
                )
            ),
            ship_counts=dict(
                Counter(
                    row.ship_role_id
                    for row in active_rows
                    if row.ship_role_id is not None
                )
            ),
            user_counts=Counter(row.user_id for row in active_rows).most_common(limit),
            bucket_series=[
                PingBucket(
                    start=bucket,
                    total=bucket_total.get(bucket, 0),
                    vp_enabled=bucket_vp.get(bucket, 0),
                    non_vp=bucket_non_vp.get(bucket, 0),
                )
                for bucket in buckets
            ],
        )

    def _query(self, filters: PingAnalyticsFilters, *, include_deleted: bool):
        query = self.session.query(RolePingLog).filter(
            RolePingLog.created_at <= filters.time_range.end,
        )
        if filters.time_range.start is not None:
            query = query.filter(RolePingLog.created_at >= filters.time_range.start)
        if not include_deleted:
            query = query.filter(RolePingLog.is_deleted.is_(False))
        if filters.ping_role_id is not None:
            query = query.filter(RolePingLog.ping_role_id == filters.ping_role_id)
        if filters.ping_type is not None:
            query = query.filter(RolePingLog.ping_type == filters.ping_type)
        if filters.ship_role_id is not None:
            query = query.filter(RolePingLog.ship_role_id == filters.ship_role_id)
        if filters.user_id is not None:
            query = query.filter(RolePingLog.user_id == filters.user_id)
        if filters.has_vp_permission is not None:
            query = query.filter(
                RolePingLog.has_vp_permission == filters.has_vp_permission
            )
        return query
