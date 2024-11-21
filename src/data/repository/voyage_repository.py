import logging
from datetime import datetime
from datetime import timedelta
from typing import Type, List

from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker, InstrumentedAttribute
from sqlalchemy.sql.functions import count

from src.data import Sailor, Voyages
from src.data.engine import engine
from src.data.models import Voyages

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

class VoyageRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def get_incommon_voyages(self, target_one: int, target_two: int) -> list[Type[Voyages]]:
        try:
            # Get all incoming voyages for target_one and target_two but only return voyages once (unique log_id)
            return self.session.query(Voyages).filter(
                    Voyages.log_id.in_(
                        self.session.query(Voyages.log_id)
                        .filter(Voyages.target_id == target_one)
                        .intersect(
                            self.session.query(Voyages.log_id)
                            .filter(Voyages.target_id == target_two)
                        )
                    )
                ).distinct(Voyages.log_id).group_by(Voyages.log_id).all()
        except Exception as e:
            log.error(f"Error getting incommon voyage log entries: {e}")
            raise e

    def get_voyages_by_log_id(self, log_id: int) -> list[Type[Voyages]]:
        try:
            return self.session.query(Voyages).filter(Voyages.log_id == log_id).all()
        except Exception as e:
            log.error(f"Error getting voyage log entries: {e}")
            raise e

    def get_most_recent_voyage(self, target_id: int) -> Type[Voyages] | None:
        try:
            return self.session.query(Voyages).filter(Voyages.target_id == target_id).order_by(Voyages.log_time.desc()).first()
        except Exception as e:
            log.error(f"Error getting most recent voyage log entry: {e}")
            raise e

    def batch_save_voyage_data(self, voyage_data: list[tuple[int, int, datetime, int]]):
        """
        Batch inserts voyage records. Ignores duplicates based on log_id and participant_id.

        Args:
            voyage_data (list): A list of tuples, where each tuple contains (log_id, target_id, datetime)
        """
        try:
            for log_id, target_id, log_time, ship_role_id in voyage_data:
                if not self.session.query(Voyages).filter_by(log_id=log_id, target_id=target_id).first():
                    self.session.add(Voyages(log_id=log_id, target_id=target_id, log_time=log_time, ship_role_id=ship_role_id))
            self.session.commit()
        except Exception as e:
            log.error(f"Error inserting voyage data: {e}")
            self.session.rollback()
            raise e

    def check_voyage_log_id_with_target_id_exists(self, log_id: int, target_id: int) -> bool:
        """
        Check if the voyage log ID exists for a specific target ID

        Args:
            log_id (int): The log ID to check.
            target_id (int): The target ID to check.
        Returns:
            bool: True if the log ID exists, False otherwise.
        """
        try:
            exists = self.session.query(Voyages).filter(Voyages.log_id == log_id,
                                                   Voyages.target_id == target_id).scalar() is not None
            return exists
        except Exception as e:
            log.error(f"Error checking if voyage log ID exists: {e}")
            self.session.rollback()
            raise e
        
    def get_sailors_by_log_id(self, log_id: int) -> list[Type[Sailor]]:
        try:
            return self.session.query(Sailor).join(Voyages).filter(Voyages.log_id == log_id).all()
        except Exception as e:
            log.error(f"Error getting sailors by log ID: {e}")
            raise e

    def get_voyages_by_target_ids_and_between_dates(self, target_ids: list[int], start_date: datetime, end_date: datetime) -> list[Type[Voyages]]:
        try:
            return self.session.query(Voyages).filter(Voyages.target_id.in_(target_ids), Voyages.log_time >= start_date, Voyages.log_time <= end_date).all()
        except Exception as e:
            log.error(f"Error getting voyage log entries by target IDs and between dates: {e}")
            raise e

    def get_voyages_by_role_ids_and_between_dates(self, role_id: list[int], start_date: datetime, end_date: datetime) -> list[Type[Voyages]]:
        try:
            return self.session.query(Voyages).filter(Voyages.ship_role_id.in_(role_id), Voyages.log_time >= start_date, Voyages.log_time <= end_date).all()
        except Exception as e:
            log.error(f"Error getting voyage log entries by role IDs and between dates: {e}")
            raise e

    def get_voyages_by_target_id_month_count(self, target_ids: list) -> dict:
        """
        Get count of voyage log entries for a target IDs in last 30 days

        Args:
            month_offset: (int) The number of months to offset the query by (default 0)
            target_ids (list): The discord IDs of the target users
        Returns:
            Voyages: Count of all voyage log entries for the target IDs
        """
        self.session = Session()
        try:
            # log_time must be within the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)

            ret = (self.session.query(Voyages.target_id, count(Voyages.target_id))
                    .filter(Voyages.target_id.in_(target_ids), Voyages.log_time >= thirty_days_ago)
                    .group_by(Voyages.target_id)
                    .all())

            return {item[0]: item[1] for item in ret}
        except Exception as e:
            log.error(f"Error getting hosted log entries: {e}")
            raise e

    def get_unique_voyages_by_target_id_month_count(self, target_ids: list) -> int:
        """
        Get count of voyage log entries for a target IDs in last 30 days

        Args:
            target_ids (list): The discord IDs of the target users
        Returns:
            Voyages: Count of all voyage log entries for the target IDs
        """
        self.session = Session()
        try:
            # log_time must be within the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)

            # select each log_id only once
            ret = (self.session.query(Voyages.log_id).distinct()
                    .filter(Voyages.target_id.in_(target_ids), Voyages.log_time >= thirty_days_ago)
                    .all())

            return len(ret)
        except Exception as e:
            log.error(f"Error getting hosted log entries: {e}")
            raise e

    def get_last_voyage_by_target_ids(self, target_ids: list) -> dict:
        """
        Get the last voyage log entry for a list of target IDs

        Args:
            target_ids (list): The discord IDs of the target users
        Returns:
            Voyages: The last voyage log entry for the target IDs
        """
        self.session = Session()
        try:
            ret = (self.session.query(Voyages.target_id, Voyages.log_time)
                    .filter(Voyages.target_id.in_(target_ids))
                    .order_by(Voyages.log_time.asc())
                    .all())

            return {item[0]: item[1] for item in ret}
        except Exception as e:
            log.error(f"Error getting hosted log entries: {e}")
            raise e

def remove_voyage_log_entries(log_id: int) -> bool:
    """
    Remove all voyage log entries for a specific log ID

    Args:
        log_id (int): The log ID to remove
    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    session = Session()
    try:
        session.execute(
            delete(Voyages).where(Voyages.log_id == log_id)
        )
        session.commit()
        return True
    except Exception as e:
        log.error(f"Error removing voyage log entries: {e}")
        session.rollback()
        raise e
    finally:
        session.close()