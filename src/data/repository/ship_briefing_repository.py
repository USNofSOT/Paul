from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from src.data.models import (
    Hosted,
    RoleChangeLog,
    RoleChangeType,
    RoleSize,
    RoleType,
    Sailor,
    Voyages,
)
from src.data.repository.common.base_repository import BaseRepository


class ShipBriefingRepository(BaseRepository[Sailor]):
    def __init__(self) -> None:
        super().__init__(Sailor)

    def get_sailors_by_ids(self, sailor_ids: list[int]) -> list[Sailor]:
        if not sailor_ids:
            return []
        return (
            self.session.query(Sailor).filter(Sailor.discord_id.in_(sailor_ids)).all()
        )

    def get_latest_voyage_activity(
        self,
        sailor_ids: list[int],
    ) -> dict[int, datetime]:
        return self._get_latest_activity(Voyages, sailor_ids)

    def get_latest_hosting_activity(
        self,
        sailor_ids: list[int],
    ) -> dict[int, datetime]:
        return self._get_latest_activity(Hosted, sailor_ids)

    def get_latest_ship_role_additions(
        self,
        *,
        ship_role_id: int,
        sailor_ids: list[int],
    ) -> dict[int, datetime]:
        if not sailor_ids:
            return {}
        rows = (
            self.session.query(
                RoleChangeLog.target_id,
                func.max(RoleChangeLog.log_time),
            )
            .filter(
                RoleChangeLog.target_id.in_(sailor_ids),
                RoleChangeLog.role_id == ship_role_id,
                RoleChangeLog.change_type == RoleChangeType.ADDED,
            )
            .group_by(RoleChangeLog.target_id)
            .all()
        )
        return {target_id: added_at for target_id, added_at in rows}

    def get_public_service_counts(
        self,
        sailor_ids: list[int],
    ) -> dict[int, int]:
        if not sailor_ids:
            return {}
        rows = (
            self.session.query(Hosted.target_id, func.count(Hosted.log_id))
            .filter(
                Hosted.target_id.in_(sailor_ids),
                Hosted.voyage_planning_message_id.isnot(None),
            )
            .group_by(Hosted.target_id)
            .all()
        )
        return {target_id: int(count) for target_id, count in rows}

    def count_voyage_logs_between(
        self,
        *,
        ship_role_id: int,
        start: datetime,
        end: datetime,
    ) -> int:
        return self._count_logs_between(
            Voyages,
            ship_role_id=ship_role_id,
            start=start,
            end=end,
        )

    def count_hosting_logs_between(
        self,
        *,
        ship_role_id: int,
        start: datetime,
        end: datetime,
    ) -> int:
        return self._count_logs_between(
            Hosted,
            ship_role_id=ship_role_id,
            start=start,
            end=end,
        )

    def _get_latest_activity(
        self,
        activity_type: type[Hosted] | type[Voyages],
        sailor_ids: list[int],
    ) -> dict[int, datetime]:
        if not sailor_ids:
            return {}
        rows = (
            self.session.query(
                activity_type.target_id,
                func.max(activity_type.log_time),
            )
            .filter(activity_type.target_id.in_(sailor_ids))
            .group_by(activity_type.target_id)
            .all()
        )
        return {target_id: activity_at for target_id, activity_at in rows}

    def _count_logs_between(
        self,
        activity_type: type[Hosted] | type[Voyages],
        *,
        ship_role_id: int,
        start: datetime,
        end: datetime,
    ) -> int:
        return int(
            self.session.query(func.count(activity_type.log_id))
            .filter(
                activity_type.ship_role_id == ship_role_id,
                activity_type.log_time >= start,
                activity_type.log_time < end,
            )
            .scalar()
            or 0
        )

    def get_ship_size_on_or_before(
        self,
        *,
        ship_role_id: int,
        before: datetime,
    ) -> int | None:
        record = (
            self.session.query(RoleSize)
            .filter(
                RoleSize.role_id == ship_role_id,
                RoleSize.role_type == RoleType.SHIP,
                RoleSize.log_time <= before,
            )
            .order_by(RoleSize.log_time.desc())
            .first()
        )
        return record.member_count if record is not None else None
