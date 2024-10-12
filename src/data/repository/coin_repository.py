import logging
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from src.data.engine import engine
from src.data.models import Coins

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

class CoinRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def save_coin(self, target_id: int, coin_type: str, moderator_id: int, old_name: str, coin_time: datetime = datetime.now()) -> Coins:
        """
        Save a coin transaction to the database.

        Args:
            target_id (int): The Discord ID of the user.
            coin_type (str): The type of coin transaction.
            moderator_id (int): The Discord ID of the moderator.
            old_name (str): The old name of the user.
            coin_time (datetime): The time of the transaction.
        Returns:
            Coins: The Coins object
        """

        try:
            coin = Coins(target_id=target_id, coin_type=coin_type, moderator_id=moderator_id, old_name=old_name, coin_time=coin_time)
            self.session.add(coin)
            self.session.commit()
            return coin
        except Exception as e:
            log.error(f"Error adding coin: {e}")
            self.session.rollback()
            raise e
        finally:
            self.session.close()
