from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.analytics.ranges import (
    TimeRange,
    bucket_start_for,
    buckets_for_observed_range,
)
from src.data.models import Hosted, Voyages, VoyageType


@dataclass(frozen=True)
class ShipAnalyticsFilters:
    time_range: TimeRange
    ship_role_id: int | None = None
    fleet_role_ids: tuple[int, ...] = ()
    voyage_type: VoyageType | None = None
    ship_name: str | None = None
    host_id: int | None = None
    crew_member_id: int | None = None


@dataclass(frozen=True)
class ShipActivityBucket:
    start: datetime
    hosted: int = 0
    voyages: int = 0


@dataclass(frozen=True)
class ShipActivityRow:
    ship_role_id: int
    hosted: int
    voyages: int


@dataclass(frozen=True)
class ShipCompanionPair:
    user_one_id: int
    user_two_id: int
    shared_voyages: int


@dataclass(frozen=True)
class ShipPair:
    ship_one_role_id: int
    ship_two_role_id: int
    shared_voyages: int


@dataclass(frozen=True)
class ShipPairing:
    ship_role_ids: tuple[int, ...]
    participant_count: int


@dataclass(frozen=True)
class ShipActivitySummary:
    filters: ShipAnalyticsFilters
    total_hosted: int
    total_voyages: int
    unique_voyage_logs: int
    ship_rows: list[ShipActivityRow]
    top_hosts: list[tuple[int, int]]
    top_voyagers: list[tuple[int, int]]
    top_companion_pairs: list[ShipCompanionPair]
    top_ship_pairs: list[ShipPair]
    top_ship_pairings: list[ShipPairing]
    ship_pairing_participants: int
    voyage_type_counts: dict[VoyageType, int]
    bucket_series: list[ShipActivityBucket]


@dataclass(frozen=True)
class ShipHistorySummary:
    filters: ShipAnalyticsFilters
    total_logs: int
    total_gold: int
    total_doubloons: int
    total_ancient_coins: int
    total_fish: int
    top_hosts: list[tuple[int, int]]
    voyage_type_counts: dict[VoyageType, int]
    recent_logs: list[int]


class ShipAnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def build_activity(
            self,
            filters: ShipAnalyticsFilters,
            *,
            limit: int = 10,
            pairing_limit: int = 5,
    ) -> ShipActivitySummary:
        hosted_rows = self._hosted_query(filters).all()
        voyage_rows = self._voyage_query(filters).all()
        filtered_log_ids = {row.log_id for row in hosted_rows} | {
            row.log_id for row in voyage_rows
        }
        pairing_hosted_rows = self._hosted_for_logs(filtered_log_ids)
        pairing_voyage_rows = self._voyages_for_logs(filtered_log_ids)

        hosted_by_ship = Counter(
            row.ship_role_id
            for row in hosted_rows
            if _is_valid_ship_role_id(row.ship_role_id)
        )
        voyages_by_ship = Counter(
            row.ship_role_id
            for row in voyage_rows
            if _is_valid_ship_role_id(row.ship_role_id)
        )
        ship_ids = sorted(set(hosted_by_ship) | set(voyages_by_ship))
        unique_voyage_logs = len(filtered_log_ids)
        companion_pairs = _top_companion_pairs(voyage_rows, pairing_limit)
        ship_pairs = _top_ship_pairs(
            pairing_hosted_rows,
            pairing_voyage_rows,
            pairing_limit,
        )
        ship_pairings, ship_pairing_participants = _top_ship_pairings(
            pairing_hosted_rows,
            pairing_voyage_rows,
            pairing_limit,
        )

        hosted_buckets: dict[datetime, int] = defaultdict(int)
        voyage_buckets: dict[datetime, int] = defaultdict(int)
        for row in hosted_rows:
            bucket = bucket_start_for(row.log_time, filters.time_range.bucket)
            hosted_buckets[bucket] += 1
        for row in voyage_rows:
            bucket = bucket_start_for(row.log_time, filters.time_range.bucket)
            voyage_buckets[bucket] += 1

        buckets = buckets_for_observed_range(
            filters.time_range,
            [row.log_time for row in hosted_rows]
            + [row.log_time for row in voyage_rows],
        )

        return ShipActivitySummary(
            filters=filters,
            total_hosted=len(hosted_rows),
            total_voyages=len(voyage_rows),
            unique_voyage_logs=unique_voyage_logs,
            ship_rows=[
                ShipActivityRow(
                    ship_role_id=ship_id,
                    hosted=hosted_by_ship.get(ship_id, 0),
                    voyages=voyages_by_ship.get(ship_id, 0),
                )
                for ship_id in ship_ids
            ],
            top_hosts=Counter(row.target_id for row in hosted_rows).most_common(limit),
            top_voyagers=Counter(row.target_id for row in voyage_rows).most_common(
                limit
            ),
            top_companion_pairs=companion_pairs,
            top_ship_pairs=ship_pairs,
            top_ship_pairings=ship_pairings,
            ship_pairing_participants=ship_pairing_participants,
            voyage_type_counts=dict(
                Counter(row.voyage_type for row in hosted_rows if row.voyage_type)
            ),
            bucket_series=[
                ShipActivityBucket(
                    start=bucket,
                    hosted=hosted_buckets.get(bucket, 0),
                    voyages=voyage_buckets.get(bucket, 0),
                )
                for bucket in buckets
            ],
        )

    def build_history(
            self,
            filters: ShipAnalyticsFilters,
            *,
            limit: int = 10,
    ) -> ShipHistorySummary:
        rows = self._hosted_query(filters).order_by(Hosted.log_time.desc()).all()
        return ShipHistorySummary(
            filters=filters,
            total_logs=len(rows),
            total_gold=sum(int(row.gold_count or 0) for row in rows),
            total_doubloons=sum(int(row.doubloon_count or 0) for row in rows),
            total_ancient_coins=sum(int(row.ancient_coin_count or 0) for row in rows),
            total_fish=sum(int(row.fish_count or 0) for row in rows),
            top_hosts=Counter(row.target_id for row in rows).most_common(limit),
            voyage_type_counts=dict(
                Counter(row.voyage_type for row in rows if row.voyage_type)
            ),
            recent_logs=[int(row.log_id) for row in rows[:limit]],
        )

    def _hosted_query(self, filters: ShipAnalyticsFilters):
        query = self.session.query(Hosted).filter(
            Hosted.log_time <= filters.time_range.end,
        )
        if filters.time_range.start is not None:
            query = query.filter(Hosted.log_time >= filters.time_range.start)
        query = self._apply_hosted_filters(query, filters)
        return query

    def _voyage_query(self, filters: ShipAnalyticsFilters):
        query = (
            self.session.query(Voyages)
            .join(Hosted, Hosted.log_id == Voyages.log_id)
            .filter(Voyages.log_time <= filters.time_range.end)
        )
        if filters.time_range.start is not None:
            query = query.filter(Voyages.log_time >= filters.time_range.start)
        if filters.ship_role_id is not None:
            query = query.filter(Voyages.ship_role_id == filters.ship_role_id)
        elif filters.fleet_role_ids:
            query = query.filter(Voyages.ship_role_id.in_(filters.fleet_role_ids))
        if filters.voyage_type is not None:
            query = query.filter(Hosted.voyage_type == filters.voyage_type)
        if filters.ship_name:
            query = query.filter(
                or_(
                    Hosted.ship_name == filters.ship_name,
                    Hosted.auxiliary_ship_name == filters.ship_name,
                )
            )
        if filters.host_id is not None:
            query = query.filter(Hosted.target_id == filters.host_id)
        if filters.crew_member_id is not None:
            query = query.filter(Voyages.target_id == filters.crew_member_id)
        return query

    def _voyages_for_logs(self, log_ids: set[int]) -> list[Voyages]:
        if not log_ids:
            return []
        return self.session.query(Voyages).filter(Voyages.log_id.in_(log_ids)).all()

    def _hosted_for_logs(self, log_ids: set[int]) -> list[Hosted]:
        if not log_ids:
            return []
        return self.session.query(Hosted).filter(Hosted.log_id.in_(log_ids)).all()

    def _apply_hosted_filters(self, query, filters: ShipAnalyticsFilters):
        if filters.ship_role_id is not None:
            query = query.filter(Hosted.ship_role_id == filters.ship_role_id)
        elif filters.fleet_role_ids:
            query = query.filter(Hosted.ship_role_id.in_(filters.fleet_role_ids))
        if filters.voyage_type is not None:
            query = query.filter(Hosted.voyage_type == filters.voyage_type)
        if filters.ship_name:
            query = query.filter(
                or_(
                    Hosted.ship_name == filters.ship_name,
                    Hosted.auxiliary_ship_name == filters.ship_name,
                )
            )
        if filters.host_id is not None:
            query = query.filter(Hosted.target_id == filters.host_id)
        if filters.crew_member_id is not None:
            query = query.filter(
                Hosted.voyages.any(Voyages.target_id == filters.crew_member_id)
            )
        return query


def _top_companion_pairs(
        rows: list[Voyages],
        limit: int,
) -> list[ShipCompanionPair]:
    users_by_log_id: dict[int, set[int]] = defaultdict(set)
    for row in rows:
        users_by_log_id[int(row.log_id)].add(int(row.target_id))

    pair_counts: Counter[tuple[int, int]] = Counter()
    for user_ids in users_by_log_id.values():
        for user_one_id, user_two_id in combinations(sorted(user_ids), 2):
            pair_counts[(user_one_id, user_two_id)] += 1

    return [
        ShipCompanionPair(
            user_one_id=user_one_id,
            user_two_id=user_two_id,
            shared_voyages=count,
        )
        for (user_one_id, user_two_id), count in pair_counts.most_common(limit)
    ]


def _top_ship_pairs(
        hosted_rows: list[Hosted],
        voyage_rows: list[Voyages],
        limit: int,
) -> list[ShipPair]:
    ships_by_log_id: dict[int, set[int]] = defaultdict(set)
    for row in hosted_rows:
        if _is_valid_ship_role_id(row.ship_role_id):
            ships_by_log_id[int(row.log_id)].add(int(row.ship_role_id))
    for row in voyage_rows:
        if _is_valid_ship_role_id(row.ship_role_id):
            ships_by_log_id[int(row.log_id)].add(int(row.ship_role_id))

    pair_counts: Counter[tuple[int, int]] = Counter()
    for ship_ids in ships_by_log_id.values():
        for ship_one_role_id, ship_two_role_id in combinations(sorted(ship_ids), 2):
            pair_counts[(ship_one_role_id, ship_two_role_id)] += 1

    return [
        ShipPair(
            ship_one_role_id=ship_one_role_id,
            ship_two_role_id=ship_two_role_id,
            shared_voyages=count,
        )
        for (ship_one_role_id, ship_two_role_id), count in pair_counts.most_common(
            limit
        )
    ]


def _top_ship_pairings(
        hosted_rows: list[Hosted],
        voyage_rows: list[Voyages],
        limit: int,
) -> tuple[list[ShipPairing], int]:
    ships_by_log_id: dict[int, set[int]] = defaultdict(set)
    participant_counts_by_log_id: Counter[int] = Counter()
    for row in hosted_rows:
        if _is_valid_ship_role_id(row.ship_role_id):
            ships_by_log_id[int(row.log_id)].add(int(row.ship_role_id))
    for row in voyage_rows:
        if _is_valid_ship_role_id(row.ship_role_id):
            log_id = int(row.log_id)
            ships_by_log_id[log_id].add(int(row.ship_role_id))
            participant_counts_by_log_id[log_id] += 1

    pairing_counts: Counter[tuple[int, ...]] = Counter()
    participant_total = 0
    for log_id, ship_ids in ships_by_log_id.items():
        participant_count = participant_counts_by_log_id[log_id]
        if participant_count <= 0:
            continue
        pairing_counts[tuple(sorted(ship_ids))] += participant_count
        participant_total += participant_count

    return (
        [
            ShipPairing(ship_role_ids=ship_role_ids, participant_count=count)
            for ship_role_ids, count in pairing_counts.most_common(limit)
        ],
        participant_total,
    )


def _is_valid_ship_role_id(role_id: int | None) -> bool:
    return role_id is not None and int(role_id) > 0
