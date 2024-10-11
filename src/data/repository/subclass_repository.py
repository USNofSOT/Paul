import datetime
import logging
from typing import Type

from sqlalchemy.orm import sessionmaker

from src.data.engine import engine
from src.data.models import Subclasses

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

def get_subclasses_by_target_id(target_id: int) -> list[Type[Subclasses]]:
    """
    Get all subclass records for a specific target ID

    Args:
        target_id (int): The Discord ID of the target user
    Returns:
        Subclasses: A list of all subclass records for the target ID
    """
    session = Session()
    try:
        return session.query(Subclasses).filter(Subclasses.target_id == target_id).all()
    except Exception as e:
        log.error(f"Error getting subclass records: {e}")
        raise e
    finally:
        session.close()

def save_subclass(author_id: int, log_id: int, target_id: int, subclass: str, log_time: datetime) -> bool:
    """
    Adds a subclass record for a member. If a record with the same target_id,
    subclass, and log_link exists, the write action is ignored to prevent duplicates.

    Args:
        author_id (int): Discord ID of the person adding the subclass record.
        log_id (int): ID of the Discord message (log) for the subclass entry.
        target_id (int): Discord ID of the member receiving the subclass entry.
        subclass (str): Name of the subclass (e.g., "Carpenter", "Flex").
        log_time (datetime): Time of the subclass entry.
    Returns:
        bool: True if the operation was successful, False otherwise.
    """

    session = Session()
    try:
        # Check if a record with the same target_id, subclass, and log_link already exists
        existing = session.query(Subclasses).filter(
            Subclasses.target_id == target_id,
            Subclasses.subclass == subclass,
            Subclasses.log_id == log_id
        ).first()

        if existing:
            log.info(f"Subclass record already exists for {target_id}, {subclass}, {log_id}")
            return False

        # Insert a new record if no duplicates are found
        session.add(Subclasses(
            author_id=author_id,
            log_id=log_id,
            target_id=target_id,
            subclass=subclass,
            log_time=log_time
        ))
        session.commit()
        return True

    except Exception as e:
        print(f"Error logging subclass: {e}")
        session.rollback()
        return False
    finally:
        session.close()