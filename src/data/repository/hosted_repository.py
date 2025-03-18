import logging
from datetime import datetime, timedelta
from typing import Any, Type

from data import VoyageType
from sqlalchemy import Row, delete, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import coalesce, count

from src.data import Sailor
from src.data.engine import engine
from src.data.models import Hosted

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)


class HostedRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def get_previous_ship_voyage_count(self, log_id: int) -> int:
        hosted = self.get_host_by_log_id(log_id)

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
                    Hosted.auxiliary_ship_name is None,
                    Hosted.log_time < hosted.log_time,
                )
                .order_by(Hosted.log_time.desc())
                .first()
            )

        return result.ship_voyage_count if result else 0

    def get_hosted_by_target_ids_and_between_dates(
        self, target_ids: list, start_date: datetime, end_date: datetime
    ) -> list[Type[Hosted]]:
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
            log.error()
            raise e

    def get_hosted_by_role_ids_and_between_dates(
        self, role_id: list[int], start_date: datetime, end_date: datetime
    ) -> list[Type[Hosted]]:
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
            log.error("Error getting hosted log entries by role IDs and between dates.")
            raise e

    def get_hosted_by_role_ids_and_target_ids_and_between_dates(
        self,
        role_id: list[int],
        target_ids: list[int],
        start_date: datetime,
        end_date: datetime,
    ) -> list[Type[Hosted]]:
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
            log.error(
                "Error getting hosted log entries by role IDs, " "target IDs, and between dates."
            )
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
    ) -> bool:
        """
        Adds a hosted data entry to the Hosted table.
        Also increments the hosted count for the target.

        Args:
            log_id (int): The log ID of the hosted data.
            target_id (int): The Discord ID of the host.
            log_time (datetime): The time of the hosted data. Defaults to the current time.
            ship_role_id (int): The role ID of the ship. Defaults to 0.
            ship_name (str): The name of the ship. Defaults to None.
            auxiliary_ship_name (str): The name of the auxiliary ship. Defaults to None.
            ship_voyage_count (int): The number of voyages the ship has made. Defaults to None.
            gold_count (int): The number of gold confiscated. Defaults to 0.
            doubloon_count (int): The number of doubloons confiscated. Defaults to 0.
            ancient_coin_count (int): The number of ancient coins confiscated. Defaults to 0.
            fish_count (int): The number of fish confiscated. Defaults to 0.
            voyage_type (VoyageType): The type of voyage. Defaults to VoyageType.UNKNOWN.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            # First, check if the log ID already exists
            if self.check_hosted_log_id_exists(log_id):
                raise ValueError(f"Log ID {log_id} already exists in the Hosted table.")
            else:
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
                        voyage_type=VoyageType(voyage_type).value
                        if voyage_type
                        else VoyageType.UNKNOWN.value,
                    )
                )

                # Increment the host count for the target
                self.session.execute(
                    update(Sailor)
                    .where(Sailor.discord_id == target_id)
                    .values({"hosted_count": coalesce(Sailor.hosted_count, 0) + 1})
                )

            self.session.commit()
            return True
        except Exception:
            log.error("Error saving hosted data.")
            self.session.rollback()
            return False

    def get_host_by_log_id(self, log_id: int) -> Hosted | None:
        try:
            return self.session.query(Hosted).filter(Hosted.log_id == log_id).first()
        except Exception as e:
            log.error("Error getting hosted data by log ID.")
            raise e

    def check_hosted_log_id_exists(self, log_id: int) -> bool:
        """
        Check if the hosted log ID exists

        Args:
            log_id (int): The log ID to check.
        Returns:
            bool: True if the log ID exists, False otherwise.
        """
        try:
            exists = self.session.query(Hosted).filter(Hosted.log_id == log_id).scalar() is not None
            return exists
        except Exception as e:
            log.error("Error checking if hosted log ID exists.")
            raise e
        finally:
            self.session.close()

    def get_hosted_by_target_ids_month_count(self, target_ids: list) -> dict:
        """
        Get count of hosted log entries for target IDs in last 30 days

        Args:
            target_ids (list): The discord IDs of the target users
        Returns:
            Hosted: Number of hosted log entries for the target IDs
        """
        self.session = Session()
        try:
            # log_time must be within the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)

            ret = (
                self.session.query(Hosted.target_id, count(Hosted.target_id))
                .filter(Hosted.target_id.in_(target_ids), Hosted.log_time >= thirty_days_ago)
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
    ):
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
            query = query.filter(Hosted.voyages.any(target_id=crew_member_id))

        return query.all()

    def get_last_hosted_by_target_ids(self, target_ids: list) -> dict:
        """
        Get the last hosted log entry for a list of target IDs

        Args:
            target_ids (list): The discord IDs of the target users
        Returns:
            Voyages: The last hosted log entry for the target IDs
        """
        self.session = Session()
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

    def retrieve_ship_history(self, ship_name: str) -> list[Type[Hosted]]:
        """
        Retrieves the ship history for the given ship name.

        Args:
            ship_name (str): The name of the ship.

        Returns:
            list[Hosted] | None: The ship history if found, otherwise None.
        """
        try:
            # Try to find info for main ship,
            # if not found, try to find info for auxiliary ship
            ship = (
                self.session.query(Hosted)
                .filter(Hosted.ship_name == ship_name, Hosted.auxiliary_ship_name is None)
                .all()
            )
            if not ship:
                ship = (
                    self.session.query(Hosted).filter(Hosted.auxiliary_ship_name == ship_name).all()
                )
            return ship
        except Exception as e:
            log.error("Error retrieving ship history.")
            raise e

    def retrieve_unique_ship_name_combinations(self) -> list[Row[tuple[Any, Any]]]:
        """
        Retrieves the unique ship name combinations from the Hosted table.
        [ship_name, auxiliary_ship_name]

        Returns:
            list[tuple[str]]: The unique ship name combinations.
        """
        try:
            return self.session.query(Hosted.ship_name, Hosted.auxiliary_ship_name).distinct().all()
        except Exception as e:
            log.error("Error retrieving unique ship name combinations.")
            raise e

def remove_hosted_entry_by_log_id(log_id: int) -> bool:
    """
    Removes the entry from the Hosted table associated with the given log_id.

    Args:
        log_id (int): The ID of the hosted voyage to remove.
    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    session = Session()
    try:
        session.execute(delete(Hosted).where(Hosted.log_id == log_id))
        session.commit()
        return True
    except Exception as e:
        log.exception("Error removing hosted entry by log ID.")
        session.rollback()
        raise e
    finally:
        session.close()
