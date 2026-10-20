from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import distinct, or_
from sqlalchemy.orm import Session

from src.analytics.ranges import (
    RANGE_OPTIONS,
    TimeRange,
    bucket_for_range,
    bucket_label,
    bucket_start_for,
    buckets_for_observed_range,
    generate_buckets,
    next_bucket_start,
    resolve_time_range,
)
from src.data.models import (
    Hosted,
    Rank,
    Sailor,
    Subclasses,
    SubclassType,
    Voyages,
    VoyageType,
)

__all__ = [
    "RANGE_OPTIONS",
    "AnalyticsFilters",
    "BucketActivity",
    "CompanionShare",
    "OverviewSummary",
    "RankShare",
    "TimeRange",
    "VoyageAnalyticsService",
    "bucket_for_range",
    "bucket_label",
    "bucket_start_for",
    "generate_buckets",
    "next_bucket_start",
    "resolve_time_range",
]


@dataclass(frozen=True)
class AnalyticsFilters:
    time_range: TimeRange
    ship_role_id: int | None = None
    user_id: int | None = None
    voyage_type: VoyageType | None = None

    @property
    def has_user_filter(self) -> bool:
        return self.user_id is not None


@dataclass(frozen=True)
class BucketActivity:
    start: datetime
    voyages: int = 0
    hosted: int = 0


@dataclass(frozen=True)
class OverviewSummary:
    filters: AnalyticsFilters
    total_voyages: int
    total_hosted: int
    unique_sailors: int
    unique_voyage_logs: int
    total_gold: int
    total_doubloons: int
    total_ancient_coins: int
    total_fish: int
    voyage_type_counts: dict[VoyageType, int]
    subclass_points: dict[SubclassType, int]
    top_voyagers: list[tuple[int, int]]
    top_hosts: list[tuple[int, int]]
    top_ships_by_voyages: list[tuple[int, int]]
    top_ships_by_hosted: list[tuple[int, int]]
    bucket_series: list[BucketActivity]


@dataclass(frozen=True)
class RankShare:
    filters: AnalyticsFilters
    rank_counts: dict[str, int]
    fallback_count: int
    unknown_count: int


@dataclass(frozen=True)
class CompanionShare:
    user_id: int
    filters: AnalyticsFilters
    shared_voyage_count: int
    companion_counts: list[tuple[int, int]]
    companion_rank_counts: dict[str, int]
    companion_ship_counts: dict[int, int]
    fallback_rank_count: int


class VoyageAnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def build_overview(
            self, filters: AnalyticsFilters, *, limit: int = 10
    ) -> OverviewSummary:
        voyage_query = self._voyage_query(filters)
        hosted_log_query = self._hosted_log_query(filters)
        hosted_by_user_query = self._hosted_by_user_query(filters)
        subclass_query = self._subclass_query(filters)

        voyage_rows = voyage_query.all()
        hosted_rows = hosted_log_query.all()
        hosted_by_user_rows = hosted_by_user_query.all()
        subclass_rows = subclass_query.all()

        voyage_type_counts = Counter(
            row.voyage_type for row in hosted_rows if row.voyage_type
        )
        subclass_points: dict[SubclassType, int] = defaultdict(int)
        for row in subclass_rows:
            if row.subclass:
                subclass_points[row.subclass] += int(row.subclass_count or 0)

        bucket_voyages: dict[datetime, int] = defaultdict(int)
        bucket_hosted: dict[datetime, int] = defaultdict(int)
        for row in voyage_rows:
            bucket_voyages[
                bucket_start_for(row.log_time, filters.time_range.bucket)
            ] += 1
        for row in hosted_by_user_rows:
            bucket_hosted[
                bucket_start_for(row.log_time, filters.time_range.bucket)
            ] += 1

        buckets = buckets_for_observed_range(
            filters.time_range,
            [row.log_time for row in voyage_rows]
            + [row.log_time for row in hosted_by_user_rows],
        )
        bucket_series = [
            BucketActivity(
                start=bucket,
                voyages=bucket_voyages.get(bucket, 0),
                hosted=bucket_hosted.get(bucket, 0),
            )
            for bucket in buckets
        ]

        return OverviewSummary(
            filters=filters,
            total_voyages=len(voyage_rows),
            total_hosted=len(hosted_by_user_rows),
            unique_sailors=len({row.target_id for row in voyage_rows}),
            unique_voyage_logs=len({row.log_id for row in voyage_rows}),
            total_gold=sum(int(row.gold_count or 0) for row in hosted_rows),
            total_doubloons=sum(int(row.doubloon_count or 0) for row in hosted_rows),
            total_ancient_coins=sum(
                int(row.ancient_coin_count or 0) for row in hosted_rows
            ),
            total_fish=sum(int(row.fish_count or 0) for row in hosted_rows),
            voyage_type_counts=dict(voyage_type_counts),
            subclass_points=dict(subclass_points),
            top_voyagers=_top_counts((row.target_id for row in voyage_rows), limit),
            top_hosts=_top_counts(
                (row.target_id for row in hosted_by_user_rows), limit
            ),
            top_ships_by_voyages=_top_counts(
                (row.ship_role_id for row in voyage_rows if row.ship_role_id), limit
            ),
            top_ships_by_hosted=_top_counts(
                (row.ship_role_id for row in hosted_by_user_rows if row.ship_role_id),
                limit,
            ),
            bucket_series=bucket_series,
        )

    def build_rank_share(self, filters: AnalyticsFilters) -> RankShare:
        voyage_rows = self._voyage_query(filters).all()
        rank_name_by_id = self._rank_name_by_id()
        rank_counts: dict[str, int] = defaultdict(int)
        fallback_count = 0
        unknown_count = 0

        for row in voyage_rows:
            rank_id = row.participant_rank_id
            if rank_id is None:
                rank_id = row.target.current_rank_id if row.target else None
                if rank_id is not None:
                    fallback_count += 1
            rank_name = rank_name_by_id.get(rank_id)
            if rank_name is None:
                unknown_count += 1
                continue
            rank_counts[rank_name] += 1

        return RankShare(
            filters=filters,
            rank_counts=dict(
                sorted(rank_counts.items(), key=lambda item: item[1], reverse=True)
            ),
            fallback_count=fallback_count,
            unknown_count=unknown_count,
        )

    def build_companion_share(
            self, filters: AnalyticsFilters, *, limit: int = 10
    ) -> CompanionShare:
        if filters.user_id is None:
            raise ValueError("Companion analytics require a user filter.")

        target_log_ids = [
            row[0]
            for row in self._voyage_query(filters)
            .with_entities(Voyages.log_id)
            .distinct()
            .all()
        ]
        if not target_log_ids:
            return CompanionShare(
                user_id=filters.user_id,
                filters=filters,
                shared_voyage_count=0,
                companion_counts=[],
                companion_rank_counts={},
                companion_ship_counts={},
                fallback_rank_count=0,
            )

        query = self.session.query(Voyages).filter(
            Voyages.log_id.in_(target_log_ids),
            Voyages.target_id != filters.user_id,
        )
        if filters.ship_role_id is not None:
            query = query.filter(Voyages.ship_role_id == filters.ship_role_id)
        rows = query.all()

        rank_name_by_id = self._rank_name_by_id()
        rank_counts: dict[str, int] = defaultdict(int)
        ship_counts: dict[int, int] = defaultdict(int)
        fallback_rank_count = 0
        for row in rows:
            if row.ship_role_id:
                ship_counts[row.ship_role_id] += 1
            rank_id = row.participant_rank_id
            if rank_id is None:
                rank_id = row.target.current_rank_id if row.target else None
                if rank_id is not None:
                    fallback_rank_count += 1
            rank_name = rank_name_by_id.get(rank_id)
            if rank_name is not None:
                rank_counts[rank_name] += 1

        return CompanionShare(
            user_id=filters.user_id,
            filters=filters,
            shared_voyage_count=len(target_log_ids),
            companion_counts=_top_counts((row.target_id for row in rows), limit),
            companion_rank_counts=dict(
                sorted(rank_counts.items(), key=lambda item: item[1], reverse=True)
            ),
            companion_ship_counts=dict(
                sorted(ship_counts.items(), key=lambda item: item[1], reverse=True)
            ),
            fallback_rank_count=fallback_rank_count,
        )

    def _voyage_query(self, filters: AnalyticsFilters):
        query = (
            self.session.query(Voyages)
            .join(Hosted, Hosted.log_id == Voyages.log_id)
            .outerjoin(Sailor, Sailor.discord_id == Voyages.target_id)
            .filter(Voyages.log_time <= filters.time_range.end)
        )
        if filters.time_range.start is not None:
            query = query.filter(Voyages.log_time >= filters.time_range.start)
        if filters.ship_role_id is not None:
            query = query.filter(Voyages.ship_role_id == filters.ship_role_id)
        if filters.user_id is not None:
            query = query.filter(Voyages.target_id == filters.user_id)
        if filters.voyage_type is not None:
            query = query.filter(Hosted.voyage_type == filters.voyage_type)
        return query

    def _hosted_log_query(self, filters: AnalyticsFilters):
        query = self.session.query(Hosted).filter(
            Hosted.log_time <= filters.time_range.end,
        )
        if filters.time_range.start is not None:
            query = query.filter(Hosted.log_time >= filters.time_range.start)
        if filters.ship_role_id is not None:
            query = query.filter(Hosted.ship_role_id == filters.ship_role_id)
        if filters.user_id is not None:
            query = query.filter(
                or_(
                    Hosted.target_id == filters.user_id,
                    Hosted.voyages.any(Voyages.target_id == filters.user_id),
                )
            )
        if filters.voyage_type is not None:
            query = query.filter(Hosted.voyage_type == filters.voyage_type)
        return query

    def _hosted_by_user_query(self, filters: AnalyticsFilters):
        query = self.session.query(Hosted).filter(
            Hosted.log_time <= filters.time_range.end,
        )
        if filters.time_range.start is not None:
            query = query.filter(Hosted.log_time >= filters.time_range.start)
        if filters.ship_role_id is not None:
            query = query.filter(Hosted.ship_role_id == filters.ship_role_id)
        if filters.user_id is not None:
            query = query.filter(Hosted.target_id == filters.user_id)
        if filters.voyage_type is not None:
            query = query.filter(Hosted.voyage_type == filters.voyage_type)
        return query

    def _subclass_query(self, filters: AnalyticsFilters):
        query = (
            self.session.query(Subclasses)
            .join(Hosted, Hosted.log_id == Subclasses.log_id)
            .filter(Subclasses.log_time <= filters.time_range.end)
        )
        if filters.time_range.start is not None:
            query = query.filter(Subclasses.log_time >= filters.time_range.start)
        if filters.ship_role_id is not None:
            query = query.filter(Hosted.ship_role_id == filters.ship_role_id)
        if filters.user_id is not None:
            query = query.filter(Subclasses.target_id == filters.user_id)
        if filters.voyage_type is not None:
            query = query.filter(Hosted.voyage_type == filters.voyage_type)
        return query

    def _rank_name_by_id(self) -> dict[int, str]:
        return {rank.role_id: rank.name for rank in self.session.query(Rank).all()}

    def available_ship_role_ids(self, filters: AnalyticsFilters) -> list[int]:
        query = self._hosted_log_query(
            AnalyticsFilters(
                time_range=filters.time_range,
                user_id=filters.user_id,
                voyage_type=filters.voyage_type,
            )
        )
        rows = query.with_entities(distinct(Hosted.ship_role_id)).all()
        return sorted(row[0] for row in rows if row[0] is not None)


def _top_counts(values, limit: int) -> list[tuple[int, int]]:
    return Counter(values).most_common(limit)
