import logging
from datetime import datetime
from typing import Type

from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from src.data import Sailor
from src.data.engine import engine
from src.data.models import Voyages

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

def check_voyage_log_id_with_target_id_exists(log_id: int, target_id: int) -> bool:
    """
    Check if the voyage log ID exists for a specific target ID

    Args:
        log_id (int): The log ID to check.
        target_id (int): The target ID to check.
    Returns:
        bool: True if the log ID exists, False otherwise.
    """
    session = Session()
    try:
        exists = session.query(Voyages).filter(Voyages.log_id == log_id, Voyages.target_id == target_id).scalar() is not None
        return exists
    except Exception as e:
        log.error(f"Error checking if voyage log ID exists: {e}")
        raise e
    finally:
        session.close()

def save_voyage(log_id: int, target_id: int, log_time: datetime) -> Voyages:
    """
    Save a voyage log entry to the database - Will also increment the voyage count for the target user

    Args:
        log_id (int): The log ID of the voyage
        target_id (int): The target ID of the sailor
        log_time (datetime): The time of the voyage

    Returns:
        Voyages: The saved voyage log entry
    """
    session = Session()
    try:
        # Ensure Sailor exists
        sailor = session.query(Sailor).filter_by(discord_id=target_id).first()
        if not sailor:
            sailor = Sailor(discord_id=target_id)
            session.add(sailor)

        # Add the voyage log entry
        session.add(Voyages(log_id=log_id, target_id=target_id, log_time=log_time))

        # Increment the voyage count
        sailor.voyage_count += 1
        session.commit()

        return Voyages(log_id=log_id, target_id=target_id, log_time=log_time)
    except Exception as e:
        log.error(f"Error saving voyage log entry: {e}")
        session.rollback()
        raise e

def get_voyages_by_target_id(target_id: int) -> list[Type[Voyages]]:
    """
    Get all voyage log entries for a specific target ID

    Args:
        target_id (int): The discord ID of the target user
    Returns:
        Voyages: A list of all voyage log entries for the target ID
    """
    session = Session()
    try:
        return session.query(Voyages).filter(Voyages.target_id == target_id).all()
    except Exception as e:
        log.error(f"Error getting voyage log entries: {e}")
        raise e
    finally:
        session.close()

def remove_voyage_by_log_id(log_id: int) -> bool:
    """
    Remove all voyage log entries for a specific log ID

    Args:
        log_id (int): The log ID to
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
        print(f"Error removing voyage log entries: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def batch_save_voyage_data(voyage_data: list[tuple[int, int, datetime]]):
    """
    Batch inserts voyage records. Ignores duplicates based on log_id and participant_id.

    Args:
        voyage_data (list): A list of tuples, where each tuple contains (log_id, target_id, datetime)
    """
    session = Session()
    try:
        for log_id, target_id, log_time in voyage_data:
            if not session.query(Voyages).filter_by(log_id=log_id, target_id=target_id).first():
                session.add(Voyages(log_id=log_id, target_id=target_id, log_time=log_time))
        session.commit()
    except Exception as e:
        log.error(f"Error inserting voyage data: {e}")
        session.rollback()
        raise e
    finally:
        session.close()

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
        return False
    finally:
        session.close()

def remove_voyage_log_entry(log_id: int, target_id: int) -> bool:
    """
    Remove a voyage log entry for a specific log ID and target ID

    Args:
        log_id (int): The log ID to remove
        target_id (int): The target ID to remove
    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    session = Session()
    try:
        session.execute(
            delete(Voyages).where(Voyages.log_id == log_id, Voyages.target_id == target_id)
        )
        session.commit()
        return True
    except Exception as e:
        log.error(f"Error removing voyage log entry: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == '__main__':
    batch_save_voyage_data([
        (55, 2, datetime.now()),
        (8, 2, datetime.now()),
        (7, 2, datetime.now()),
    ])