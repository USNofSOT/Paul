import logging

from src.data.models import RankHistory
from src.data.repository.common.base_repository import BaseRepository
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)


class RankHistoryRepository(BaseRepository[RankHistory]):
    def __init__(self):
        super().__init__(RankHistory)

    def log_rank_change(self, sailor_id: int, rank_id: int, reason: str = None):
        """
        Logs a rank change for a sailor.

        Args:
            sailor_id (int): The Discord ID of the sailor.
            rank_id (int): The ID of the new rank.
            reason (str, optional): The reason for the rank change. Defaults to None.
        """
        try:
            rank_history = RankHistory(
                sailor_id=sailor_id,
                rank_id=rank_id,
                reason=reason,
                log_time=utc_time_now()
            )
            self.session.add(rank_history)
            self.session.commit()
        except Exception as e:
            log.error(f"Error logging rank change for sailor {sailor_id} to rank {rank_id}: {e}")
            self.session.rollback()
            raise e
