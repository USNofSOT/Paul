from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from src.analytics.ranges import (
    TimeRange,
    buckets_for_observed_range,
    next_bucket_start,
)
from src.data.models import RoleSize, RoleType


@dataclass(frozen=True)
class RoleSizeAnalyticsFilters:
    time_range: TimeRange
    role_ids: tuple[int, ...]
    role_type: RoleType | None = None


@dataclass(frozen=True)
class RoleSizePoint:
    start: datetime
    member_count: int


@dataclass(frozen=True)
class RoleSizeAnalyticsSummary:
    filters: RoleSizeAnalyticsFilters
    series: dict[int, list[RoleSizePoint]]


class RoleSizeAnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def build_summary(
            self,
            filters: RoleSizeAnalyticsFilters,
    ) -> RoleSizeAnalyticsSummary:
        series: dict[int, list[RoleSizePoint]] = {}
        for role_id in filters.role_ids:
            rows = self._rows_for_role(role_id, filters)
            buckets = buckets_for_observed_range(
                filters.time_range,
                [row.log_time for row in rows],
            )
            points = []
            for bucket in buckets:
                points.append(
                    RoleSizePoint(
                        start=bucket,
                        member_count=_estimate_size_at(
                            rows,
                            bucket,
                            next_bucket_start(bucket, filters.time_range.bucket),
                        ),
                    )
                )
            series[role_id] = points
        return RoleSizeAnalyticsSummary(filters=filters, series=series)

    def _rows_for_role(
            self,
            role_id: int,
            filters: RoleSizeAnalyticsFilters,
    ) -> list[RoleSize]:
        query = self.session.query(RoleSize).filter(RoleSize.role_id == role_id)
        if filters.role_type is not None:
            query = query.filter(RoleSize.role_type == filters.role_type)
        query = query.filter(RoleSize.log_time <= filters.time_range.end)
        return query.order_by(RoleSize.log_time.asc()).all()


def _estimate_size_at(
        rows: list[RoleSize],
        bucket_start: datetime,
        bucket_end: datetime,
) -> int:
    in_bucket = [
        row.member_count for row in rows if bucket_start <= row.log_time < bucket_end
    ]
    if in_bucket:
        return int(in_bucket[-1])
    before = [row.member_count for row in rows if row.log_time < bucket_start]
    return int(before[-1]) if before else 0
