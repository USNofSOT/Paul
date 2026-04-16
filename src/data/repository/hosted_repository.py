import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict

from sqlalchemy import Row, delete, update
from sqlalchemy.sql.functions import coalesce, count

from src.data import Sailor
from src.data import VoyageType
from src.data.models import Hosted
from src.data.repository.common.base_repository import BaseRepository, Session

log = logging.getLogger(__name__)


class HostedRepository(BaseRepository[Hosted]):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(Hosted, session)

    def get_previous_ship_voyage_count(self, log_id: int) -> int:
        hosted = self.get_host_by_log_id(log_id)
        if not hosted:
            return 0

        if hosted.auxiliary_ship_name:
            result = (
                self.session.query(Hosted)
                .filter(
                    Hosted.ship_name == hosted.ship_name,
                    Hosted.auxiliary_ship_name == hosted.auxiliary_ship_name,
                    Hosted.log_time < hosted.log_time,
                )
                .order_by(Hosted.log_time.desc())
                .first()
            )
        else:
            result = (
                self.session.query(Hosted)
                .filter(
                    Hosted.ship_name == hosted.ship_name,
                    Hosted.auxiliary_ship_name.is_(None),
                    Hosted.log_time < hosted.log_time,
                )
                .order_by(Hosted.log_time.desc())
                .first()
            )

        return result.ship_voyage_count if result else 0

    def get_hosted_by_target_ids_and_between_dates(
            self, target_ids: list[int], start_date: datetime, end_date: datetime
    ) -> list[Hosted]:
        try:
            return (
                self.session.query(Hosted)
                .filter(
                    Hosted.target_id.in_(target_ids),
                    Hosted.log_time >= start_date,
                    Hosted.log_time <= end_date,
                )
                .all()
            )
        except Exception as e:
            log.error("Error getting hosted log entries by target IDs and dates.")
            raise e

    def get_hosted_by_role_ids_and_between_dates(
        self, role_id: list[int], start_date: datetime, end_date: datetime
    ) -> list[Hosted]:
        try:
            return (
                self.session.query(Hosted)
                .filter(
                    Hosted.ship_role_id.in_(role_id),
                    Hosted.log_time >= start_date,
                    Hosted.log_time <= end_date,
                )
                .all()
            )
        except Exception as e:
            log.error("Error getting hosted log entries by role IDs and dates.")
            raise e

    def get_hosted_by_role_ids_and_target_ids_and_between_dates(
        self,
        role_id: list[int],
        target_ids: list[int],
        start_date: datetime,
        end_date: datetime,
    ) -> list[Hosted]:
        try:
            return (
                self.session.query(Hosted)
                .filter(
                    Hosted.ship_role_id.in_(role_id),
                    Hosted.target_id.in_(target_ids),
                    Hosted.log_time >= start_date,
                    Hosted.log_time <= end_date,
                )
                .all()
            )
        except Exception as e:
            log.error("Error getting hosted log entries by role, targets, and dates.")
            raise e

    def save_hosted_data(
        self,
        log_id: int,
        target_id: int,
        log_time: datetime = datetime.now(),
        ship_role_id: int = 0,
        ship_name: str = None,
        auxiliary_ship_name: str = None,
        ship_voyage_count: int = None,
        gold_count: int = 0,
        doubloon_count: int = 0,
        ancient_coin_count: int = 0,
        fish_count: int = 0,
        voyage_type: VoyageType = None,
            voyage_planning_channel_id: int = None,
            voyage_planning_message_id: int = None,
    ) -> bool:
        try:
            if self.check_hosted_log_id_exists(log_id):
                raise ValueError(f"Log ID {log_id} already exists in the Hosted table.")

            # Standardization for voyage_type enum
            resolved_voyage_type = voyage_type or VoyageType.UNKNOWN
            if isinstance(resolved_voyage_type, str):
                resolved_voyage_type = VoyageType(resolved_voyage_type)

            self.session.add(
                Hosted(
                    log_id=log_id,
                    target_id=target_id,
                    log_time=log_time,
                    ship_role_id=ship_role_id,
                    ship_name=ship_name,
                    auxiliary_ship_name=auxiliary_ship_name,
                    ship_voyage_count=ship_voyage_count,
                    gold_count=gold_count,
                    doubloon_count=doubloon_count,
                    ancient_coin_count=ancient_coin_count,
                    fish_count=fish_count,
                    voyage_type=resolved_voyage_type,
                    voyage_planning_channel_id=voyage_planning_channel_id,
                    voyage_planning_message_id=voyage_planning_message_id,
                )
            )

            # Increment the host count for the target
            self.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values(
                    {
                        "hosted_count": coalesce(Sailor.hosted_count, 0) + 1,
                        "last_hosting_at": log_time,
                    }
                )
            )

            self.session.commit()
            return True
        except Exception as e:
            log.error(f"Error saving hosted data: {e}")
            self.session.rollback()
            return False

    def get_count_hosted_in_vp_by_member_id(self, member_id: int) -> int:
        try:
            return (
                self.session.query(Hosted)
                .filter(
                    Hosted.voyage_planning_message_id.isnot(None),
                    Hosted.target_id == member_id
                )
                .count()
            )
        except Exception as e:
            log.error("Error getting hosted data in voyage planning by member ID.")
            raise e

    def get_host_by_log_id(self, log_id: int) -> Hosted | None:
        try:
            return self.session.query(Hosted).filter(Hosted.log_id == log_id).first()
        except Exception as e:
            log.error("Error getting hosted data by log ID.")
            raise e

    def check_hosted_log_id_exists(self, log_id: int) -> bool:
        try:
            return (
                    self.session.query(Hosted.log_id).filter(Hosted.log_id == log_id).first()
                is not None
            )
        except Exception as e:
            log.error("Error checking if hosted log ID exists.")
            raise e

    def get_hosted_by_target_ids_month_count(self, target_ids: list[int]) -> Dict[int, int]:
        try:
            # log_time must be within the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)

            ret = (
                self.session.query(Hosted.target_id, count(Hosted.target_id))
                .filter(
                    Hosted.target_id.in_(target_ids), Hosted.log_time >= thirty_days_ago
                )
                .group_by(Hosted.target_id)
                .all()
            )

            return {item[0]: item[1] for item in ret}
        except Exception as e:
            log.error("Error getting hosted log entries by target IDs and month count.")
            raise e

    def get_filtered_hosted(
        self,
        main_ship=None,
        auxiliary_ship=None,
        ship_role_id=None,
        voyage_type=None,
        host_id=None,
        crew_member_id=None,
    ) -> list[Hosted]:
        query = self.session.query(Hosted).order_by(Hosted.log_time.desc())

        if main_ship:
            query = query.filter(
                Hosted.ship_name == main_ship, Hosted.auxiliary_ship_name.is_(None)
            )
        if auxiliary_ship:
            query = query.filter(Hosted.auxiliary_ship_name == auxiliary_ship)
        if ship_role_id:
            query = query.filter(Hosted.ship_role_id == ship_role_id)
        if voyage_type:
            query = query.filter(Hosted.voyage_type == voyage_type)
        if host_id:
            query = query.filter(Hosted.target_id == host_id)
        if crew_member_id:
            from src.data.models import Voyages
            query = query.join(Voyages, Hosted.log_id == Voyages.log_id).filter(Voyages.target_id == crew_member_id)

        return query.all()

    def get_last_hosted_by_target_ids(self, target_ids: list[int]) -> Dict[int, datetime]:
        try:
            ret = (
                self.session.query(Hosted.target_id, Hosted.log_time)
                .filter(Hosted.target_id.in_(target_ids))
                .order_by(Hosted.log_time.asc())
                .all()
            )

            return {item[0]: item[1] for item in ret}
        except Exception as e:
            log.error("Error getting last hosted log entries.")
            raise e

    def retrieve_ship_history(self, ship_name: str) -> list[Hosted]:
        try:
            # Try to find info for main ship,
            # if not found, try to find info for auxiliary ship
            ship = (
                self.session.query(Hosted)
                .filter(
                    Hosted.ship_name == ship_name, Hosted.auxiliary_ship_name.is_(None)
                )
                .all()
            )
            if not ship:
                ship = (
                    self.session.query(Hosted)
                    .filter(Hosted.auxiliary_ship_name == ship_name)
                    .all()
                )
            return ship
        except Exception as e:
            log.error("Error retrieving ship history.")
            raise e

    def retrieve_unique_ship_name_combinations(self) -> list[Row[tuple[Any, Any]]]:
        try:
            return (
                self.session.query(Hosted.ship_name, Hosted.auxiliary_ship_name)
                .distinct()
                .all()
            )
        except Exception as e:
            log.error("Error retrieving unique ship name combinations.")
            raise e

    def remove_hosted_entry_by_log_id(self, log_id: int) -> bool:
        try:
            self.session.execute(delete(Hosted).where(Hosted.log_id == log_id))
            self.session.commit()
            return True
        except Exception as e:
            log.exception(f"Error removing hosted entry {log_id}")
            self.session.rollback()
            raise e


def remove_hosted_entry_by_log_id(log_id: int) -> bool:
    """
    Removes the entry from the Hosted table associated with the given log_id.
    """
    with HostedRepository() as repo:
        return repo.remove_hosted_entry_by_log_id(log_id)
