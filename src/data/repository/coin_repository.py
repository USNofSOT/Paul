import logging
from datetime import datetime

from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
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

    def save_coin(self, target_id: int, coin_type: str, moderator_id: int, old_name: str, coin_time: datetime = None) -> Coins:
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
        coin_time = coin_time or datetime.now()

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

    def remove_coin(self, coin: Coins) -> None:
        """
        Remove a coin transaction from the database.

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
            self.session.delete(coin)
            self.session.commit()
        except Exception as e:
            log.error(f"Error removing coin: {e}")
            self.session.rollback()
            raise e
        finally:
            self.session.close()

    def find_coin_by_target_and_moderator_and_type(self, target_id: int, moderator_id: int, coin_type: str) -> Coins or None:
        """
        Find a coin transaction by target and moderator IDs.

        Args:
            target_id (int): The Discord ID of the user.
            moderator_id (int): The Discord ID of the moderator.
        Returns:
            Coins: The Coins object
        """

        try:
            coin = self.session.query(Coins).filter_by(target_id=target_id, moderator_id=moderator_id, coin_type=coin_type).first()
            return coin
        except Exception as e:
            log.error(f"Error finding coin: {e}")
            raise e
        finally:
            self.session.close()
    
    def find_coin_by_target_and_OldName_and_type(self, target_id: int, old_name: str, coin_type: str) -> Coins or None:
        """
        Find a coin transaction by target and moderator IDs.

        Args:
            target_id (int): The Discord ID of the user.
            oldname (str): The Discord ID of the moderator.
        Returns:
            Coins: The Coins object
        """

        try:
            coin = self.session.query(Coins).filter_by(target_id=target_id, old_name=old_name, coin_type=coin_type).first()
            return coin
        except Exception as e:
            log.error(f"Error finding coin: {e}")
            raise e
        finally:
            self.session.close()

    def get_coins_by_target(self, target_id):
        """
        Fetches and categorizes coins for a target.

        Args:
            target_id: The ID of the target.

        Returns:
            A tuple containing two lists: regular_coins and commander_coins.
        """
        
        try:
            regular_coins = []
            commander_coins = []

            with Session() as session:
                coins = session.query(Coins).filter(Coins.target_id == target_id).all()
                for coin in coins:
                    if coin.coin_type == "Regular Challenge Coin":
                        regular_coins.append(coin)
                    elif coin.coin_type == "Commanders Challenge Coin":
                        commander_coins.append(coin)

            return regular_coins, commander_coins
        except Exception as e:
            log.error(f"Error retriving coins by user: {e}")
        finally:
            self.session.close()

    def get_top_coin_holders(self, limit, member_list):
        """
         Gets the top coin holders.

         Args:
            limit: The maximum number of coin holders to return.

         Returns:
            A list of tuples, where each tuple contains the target_id and their total coin count.
        """
        if limit == None:
            limit = 3
        try:
                results = self.session.query(
            Coins.target_id, func.count(Coins.target_id).label('total_coins')
        ).group_by(Coins.target_id).filter(Coins.target_id.in_(member_list)).order_by(func.count(Coins.target_id).desc()).limit(limit).all()
                return results
        
        except Exception as e:
            log.error(f"Error getting top coin holders: {e}")
        finally:
            self.session.close()