import logging
from datetime import datetime
from typing import Optional

from src.data.models import ForceAdd
from src.data.repository.common.base_repository import BaseRepository, Session

log = logging.getLogger(__name__)


class ForceAddRepository(BaseRepository[ForceAdd]):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(ForceAdd, session)

    def save_forceadd(self, target_id: int, add_type: str, amount: int, moderator_id: int,
                      add_time: datetime = None) -> ForceAdd:
        add_time = add_time or datetime.now()
        try:
            forceadd = ForceAdd(target_id=target_id, add_type=add_type, amount=amount, moderator_id=moderator_id,
                                add_time=add_time)
            self.session.add(forceadd)
            self.session.commit()
            return forceadd
        except Exception as e:
            log.error(f"Error adding force add: {e}")
            self.session.rollback()
            raise e


def save_forceadd(target_id: int, type: str, amount: int, moderator_id: int, add_time: datetime = None) -> ForceAdd:
    """
    Log a force add transaction
    """
    with ForceAddRepository() as repo:
        return repo.save_forceadd(target_id=target_id, add_type=type, amount=amount, moderator_id=moderator_id,
                                  add_time=add_time)
