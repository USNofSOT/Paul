import logging

from sqlalchemy import update, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import coalesce

from engine import engine
from models import Voyages

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

def remove_voyage_log_entries(log_id: int) -> bool:
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
