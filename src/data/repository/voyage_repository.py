import logging
from datetime import datetime
from typing import Type

from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from src.data.engine import engine
from src.data.models import Voyages

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

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


if __name__ == '__main__':
    batch_save_voyage_data([
        (55, 2, datetime.now()),
        (8, 2, datetime.now()),
        (7, 2, datetime.now()),
    ])