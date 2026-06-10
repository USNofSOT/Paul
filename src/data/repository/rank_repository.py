import logging

from src.data.models import Rank
from src.data.repository.common.base_repository import BaseRepository

log = logging.getLogger(__name__)


class RankRepository(BaseRepository[Rank]):
    def __init__(self):
        super().__init__(Rank)

    def get_rank_by_role_id(self, role_id: int) -> Rank | None:
        """
        Retrieves a Rank by its Discord role ID.

        Args:
            role_id (int): The Discord role ID.
        Returns:
            Rank | None: The Rank object if found, otherwise None.
        """
        try:
            return self.session.query(Rank).filter(Rank.role_id == role_id).first()
        except Exception as e:
            log.error(f"Error retrieving Rank by role_id {role_id}: {e}")
            return None

    def get_all_ranks(self) -> list[Rank]:
        """
        Retrieves all Rank objects.

        Returns:
            list[Rank]: A list of all Rank objects.
        """
        try:
            return self.session.query(Rank).all()
        except Exception as e:
            log.error(f"Error retrieving all Ranks: {e}")
            return []

    def save_rank(self, rank: Rank):
        """
        Saves a Rank object to the database.

        Args:
            rank (Rank): The Rank object to save.
        """
        try:
            self.session.add(rank)
            self.session.commit()
        except Exception as e:
            log.error(f"Error saving Rank: {e}")
            self.session.rollback()
            raise e
