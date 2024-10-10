import logging
from datetime import datetime
from typing import Type

from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from src.data.engine import engine
from src.data.models import Hosted

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

def get_hosted_by_target_id(target_id: int) -> list[Type[Hosted]]:
    """
    Get all hosted log entries for a specific target ID

    Args:
        target_id (int): The discord ID of the target user
    Returns:
        Hosted: A list of all hosted log entries for the target ID
    """
    session = Session()
    try:
        return session.query(Hosted).filter(Hosted.target_id == target_id).all()
    except Exception as e:
        log.error(f"Error getting hosted log entries: {e}")
        raise e
    finally:
        session.close()

def check_hosted_log_id_exists(log_id: int) -> bool:
    """
    Check if the hosted log ID exists

    Args:
        log_id (int): The log ID to check.
    Returns:
        bool: True if the log ID exists, False otherwise.
    """
    session = Session()
    try:
        exists = session.query(Hosted).filter(Hosted.log_id == log_id).scalar() is not None
        return exists
    except Exception as e:
        log.error(f"Error checking if hosted log ID exists: {e}")
        raise e
    finally:
        session.close()

def save_hosted_data(log_id: int, target_id: int, log_time: datetime = datetime.now()) -> bool:
    """
    Adds a hosted data entry to the Hosted table.

    Args:
        log_id (int): The log ID of the hosted data.
        target_id (int): The Discord ID of the host.
        log_time (datetime): The time of the hosted data. Defaults to the current time.
    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    session = Session()
    try:
        session.add(Hosted(log_id=log_id, target_id=target_id, log_time=log_time))
        session.commit()
        return True
    except Exception as e:
        print(f"Error adding hosted data: {e}")
        session.rollback()
        return False
    finally:
        session.close()

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
        return False
    finally:
        session.close()