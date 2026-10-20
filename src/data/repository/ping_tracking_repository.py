import logging
from datetime import datetime
from sqlalchemy import update
from sqlalchemy.dialects.mysql import insert

from src.data.models import RolePingLog
from src.data.repository.common.base_repository import BaseRepository

log = logging.getLogger(__name__)

class PingTrackingRepository(BaseRepository[RolePingLog]):
    def __init__(self):
        super().__init__(RolePingLog)

    def log_pings_bulk(self, pings_data: list[dict]) -> bool:
        if not pings_data:
            return True
            
        try:
            # IGNORE safely skips just the duplicate rows and inserts the valid ones.
            insert_stmt = insert(RolePingLog).values(pings_data).prefix_with("IGNORE")
            
            self.session.execute(insert_stmt)
            self.session.commit()
            
            return True
            
        except Exception as e:
            self.session.rollback()
            log.error(f"Error bulk logging pings: {e}", extra={"notify_engineer": True})
            raise e

    def mark_as_deleted(self, message_id: int) -> int:
        try:
            result = self.session.execute(
                update(RolePingLog)
                .where(RolePingLog.message_id == message_id)
                .values(is_deleted=True)
            )
            self.session.commit()
            return result.rowcount
        except Exception as e:
            self.session.rollback()
            log.error(f"Error marking ping logs as deleted for message {message_id}: {e}", extra={"notify_engineer": True})
            raise e

    def get_active_ping_logs_since(self, since: datetime) -> list[RolePingLog]:
        try:
            return self.session.query(RolePingLog).filter(
                RolePingLog.created_at >= since,
                RolePingLog.is_deleted == False
            ).all()
        except Exception as e:
            self.session.rollback()
            log.error(f"Error fetching ping logs since {since}: {e}", extra={"notify_engineer": True})
            raise e
