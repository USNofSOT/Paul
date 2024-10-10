import logging

from sqlalchemy import update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import coalesce

from engine import engine
from models import Coins

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

def log_coin(target_id: int, coin_type: str, moderator_id: int, old_name: str, coin_time: str) -> bool:
    """
    Log a coin transaction

    Args:
        target_id (int): The Discord ID of the user.
        coin_type (str): The type of coin transaction.
        moderator_id (int): The Discord ID of the moderator.
        old_name (str): The old name of the user.
        coin_time (str): The time of the transaction.
    """
    session = Session()
    try:
        session.add(Coins(target_id=target_id, coin_type=coin_type, moderator_id=moderator_id, old_name=old_name, coin_time=coin_time))
        session.commit()
        return True
    except Exception as e:
        print(f"Error adding coin: {e}")
        session.rollback()
        return False
    finally:
        session.close()