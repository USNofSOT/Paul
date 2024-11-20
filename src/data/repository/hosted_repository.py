import logging
from datetime import datetime
from datetime import timedelta
from typing import Type

from sqlalchemy import delete, update
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

    def get_hosted_by_target_ids_and_between_dates(self, target_ids: list, start_date: datetime, end_date: datetime) -> list[Type[Hosted]]:
        try:
            return self.session.query(Hosted).filter(Hosted.target_id.in_(target_ids), Hosted.log_time >= start_date, Hosted.log_time <= end_date).all()
        except Exception as e:
            log.error(f"Error getting voyage log entries by target IDs and between dates: {e}")
            raise e

    def save_hosted_data(self, log_id: int, target_id: int, log_time: datetime = datetime.now(), ship_role_id: int = 0) -> bool:
        """
        Adds a hosted data entry to the Hosted table. Also increments the hosted count for the target.

        Args:
            log_id (int): The log ID of the hosted data.
            target_id (int): The Discord ID of the host.
            log_time (datetime): The time of the hosted data. Defaults to the current time.
            ship_role_id (int): The role ID of the ship. Defaults to 0.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            # First, check if the log ID already exists
            if self.check_hosted_log_id_exists(log_id):
                raise ValueError(f"Log ID {log_id} already exists in the Hosted table.")
            else:
                self.session.add(Hosted(log_id=log_id, target_id=target_id, log_time=log_time, ship_role_id=ship_role_id))

                # Increment the host count for the target
                self.session.execute(
                    update(Sailor)
                    .where(Sailor.discord_id == target_id)
                    .values({
                        "hosted_count": coalesce(Sailor.hosted_count, 0) + 1
                    })
                )

            self.session.commit()
            return True
        except Exception as e:
            log.error(f"Error saving hosted data: {e}")
            self.session.rollback()
            return False
        
    def get_host_by_log_id(self, log_id: int) -> Hosted | None:
        try:
            return self.session.query(Hosted).filter(Hosted.log_id == log_id).first()
        except Exception as e:
            log.error(f"Error getting hosted log entry: {e}")
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
            log.error(f"Error checking if hosted log ID exists: {e}")
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

            ret = (self.session.query(Hosted.target_id, count(Hosted.target_id))
                .filter(Hosted.target_id.in_(target_ids), Hosted.log_time >= thirty_days_ago)
                .group_by(Hosted.target_id)
                .all())

            return {item[0]: item[1] for item in ret}
        except Exception as e:
            log.error(f"Error getting hosted log entries: {e}")
            raise e

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
            ret = (self.session.query(Hosted.target_id, Hosted.log_time)
                    .filter(Hosted.target_id.in_(target_ids))
                    .order_by(Hosted.log_time.asc())
                    .all())

            return {item[0]: item[1] for item in ret}
        except Exception as e:
            log.error(f"Error getting hosted log entries: {e}")
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
        session.execute(
            delete(Hosted).where(Hosted.log_id == log_id)
        )
        session.commit()
        return True
    except Exception as e:
        print(f"Error removing hosted entry: {e}")
        session.rollback()
        raise e
    finally:
        session.close()