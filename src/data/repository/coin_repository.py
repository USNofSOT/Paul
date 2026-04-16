import logging
from datetime import datetime
from typing import Optional, List, Tuple

from sqlalchemy import func

from src.data.models import Coins
from src.data.repository.common.base_repository import BaseRepository, Session

log = logging.getLogger(__name__)


class CoinRepository(BaseRepository[Coins]):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(Coins, session)

    def save_coin(
        self,
        target_id: int,
        coin_type: str,
        moderator_id: int,
        old_name: str,
        coin_time: datetime = None,
    ) -> Coins:
        """
        Save a coin transaction to the database.
        """
        coin_time = coin_time or datetime.now()

        try:
            coin = Coins(
                target_id=target_id,
                coin_type=coin_type,
                moderator_id=moderator_id,
                old_name=old_name,
                coin_time=coin_time,
            )
            self.session.add(coin)
            self.session.commit()
            return coin
        except Exception as e:
            log.error("Error adding coin: %s", e)
            self.session.rollback()
            raise e

    def remove_coin(self, coin: Coins) -> None:
        """
        Remove a coin transaction from the database.
        """
        try:
            self.session.delete(coin)
            self.session.commit()
        except Exception as e:
            log.error("Error removing coin: %s", e)
            self.session.rollback()
            raise e

    def find_coin_by_target_and_moderator_and_type(
        self, target_id: int, moderator_id: int, coin_type: str
    ) -> Optional[Coins]:
        """
        Find a coin transaction by target and moderator IDs.
        """
        try:
            coin = (
                self.session.query(Coins)
                .filter_by(
                    target_id=target_id, moderator_id=moderator_id, coin_type=coin_type
                )
                .first()
            )
            return coin
        except Exception as e:
            log.error("Error finding coin: %s", e)
            self.session.rollback()
            raise e

    def find_coin_by_target_and_OldName_and_type(  # noqa
        self, target_id: int, old_name: str, coin_type: str
    ) -> Optional[Coins]:
        """
        Find a coin transaction by target and old name.
        """
        try:
            coin = (
                self.session.query(Coins)
                .filter_by(target_id=target_id, old_name=old_name, coin_type=coin_type)
                .first()
            )
            return coin
        except Exception as e:
            log.error("Error finding coin by target and old name: %s", e)
            self.session.rollback()
            raise e

    def get_coins_by_target(self, target_id: int) -> Tuple[List[Coins], List[Coins]]:
        """
        Fetches and categorizes coins for a target.
        """
        try:
            coins = self.session.query(Coins).filter(Coins.target_id == target_id).all()
            regular_coins = [c for c in coins if c.coin_type == "Regular Challenge Coin"]
            commander_coins = [c for c in coins if c.coin_type == "Commanders Challenge Coin"]
            return regular_coins, commander_coins
        except Exception as e:
            log.error("Error retrieving coins by user: %s", e)
            self.session.rollback()
            return [], []

    def get_top_coin_holders(self, limit: int, member_list: List[int]) -> List[Tuple[int, int]]:
        """
        Gets the top coin holders.
        """
        if limit is None:
            limit = 3
        try:
            results = (
                self.session.query(
                    Coins.target_id, func.count(Coins.target_id).label("total_coins")
                )
                .group_by(Coins.target_id)
                .filter(Coins.target_id.in_(member_list))
                .order_by(func.count(Coins.target_id).desc())
                .limit(limit)
                .all()
            )
            return results
        except Exception as e:
            log.error("Error getting top coin holders: %s", e)
            self.session.rollback()
            return []
