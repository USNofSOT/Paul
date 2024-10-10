import logging
from datetime import datetime
from xmlrpc.client import DateTime

from sqlalchemy import update, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import coalesce

from engine import engine
from models import Hosted

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

def hosted_log_id_exists(log_id: int) -> bool:
    session = Session()
    try:
        exists = session.query(Hosted).filter(Hosted.log_id == log_id).scalar() is not None
        return exists
    except Exception as e:
        print(f"Error checking if hosted log ID exists: {e}")
        return False
    finally:
        session.close()

def log_hosted_data(log_id: int, target_id: int, log_time: datetime = datetime.now()) -> bool:
    """
    Log hosted data

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

def remove_hosted_entry(log_id: int) -> bool:
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