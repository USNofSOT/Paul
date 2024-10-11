import logging
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from src.data.engine import engine
from src.data.models import ForceAdd

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

def  save_forceadd(target_id: int, type: str, amount: int, moderator_id: int, add_time: datetime = datetime.now()) -> ForceAdd:
    """
    Log a force add transaction

    Args:
        target_id (int): The Discord ID of the user.
        type (str): The type of force add transaction.
        amount (int): The amount of coins to add.
        moderator_id (int): The Discord ID of the moderator.
        add_time (datetime): The time of the transaction.
    Returns:
        ForceAdd: The ForceAdd object
    """
    session = Session()
    try:
        forceadd = ForceAdd(target_id=target_id, add_type=type, amount=amount, moderator_id=moderator_id, add_time=add_time)
        session.add(forceadd)
        session.commit()
        return forceadd
    except Exception as e:
        log.error(f"Error adding force add: {e}")
        session.rollback()
        raise e
    finally:
        session.close()

if __name__ == '__main__':
    log_forceadd(123, "test", 100, 2)