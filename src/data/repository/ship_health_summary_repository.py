from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from src.data.models import Hosted, Sailor, ShipSize, Voyages
from src.data.repository.common.base_repository import BaseRepository


class ShipHealthSummaryRepository(BaseRepository[Sailor]):
    def __init__(self) -> None:
        super().__init__(Sailor)

    def get_sailors_by_ids(self, sailor_ids: list[int]) -> list[Sailor]:
        if not sailor_ids:
            return []
        return (
            self.session.query(Sailor)
            .filter(Sailor.discord_id.in_(sailor_ids))
            .all()
        )

    def count_recent_voyage_logs(self, *, ship_role_id: int, since: datetime) -> int:
        return int(
            self.session.query(func.count(Voyages.log_id))
            .filter(
                Voyages.ship_role_id == ship_role_id,
                Voyages.log_time >= since,
            )
            .scalar()
            or 0
        )

    def count_recent_hosting_logs(self, *, ship_role_id: int, since: datetime) -> int:
        return int(
            self.session.query(func.count(Hosted.log_id))
            .filter(
                Hosted.ship_role_id == ship_role_id,
                Hosted.log_time >= since,
            )
            .scalar()
            or 0
        )

    def count_voyage_logs_between(
            self,
            *,
            ship_role_id: int,
            start: datetime,
            end: datetime,
    ) -> int:
        return int(
            self.session.query(func.count(Voyages.log_id))
            .filter(
                Voyages.ship_role_id == ship_role_id,
                Voyages.log_time >= start,
                Voyages.log_time < end,
            )
            .scalar()
            or 0
        )

    def count_hosting_logs_between(
            self,
            *,
            ship_role_id: int,
            start: datetime,
            end: datetime,
    ) -> int:
        return int(
            self.session.query(func.count(Hosted.log_id))
            .filter(
                Hosted.ship_role_id == ship_role_id,
                Hosted.log_time >= start,
                Hosted.log_time < end,
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
            self.session.query(ShipSize)
            .filter(
                ShipSize.ship_role_id == ship_role_id,
                ShipSize.log_time <= before,
            )
            .order_by(ShipSize.log_time.desc())
            .first()
        )
        return record.member_count if record is not None else None
