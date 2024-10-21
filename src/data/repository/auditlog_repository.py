import datetime
import logging

from sqlalchemy.orm import sessionmaker

from src.data import NameChangeLog, AuditLog, RoleChangeLog, RoleChangeType, TimeoutLog
from src.data.engine import engine
from src.data.repository.sailor_repository import ensure_sailor_exists
from src.utils.time_utils import time_now

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

class AuditLogRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def log_role_change(self, target_id: int, changed_by_id: int, guild_id: int, role_id: int, role_name: str, action: RoleChangeType) -> RoleChangeLog:
        try:
            log_entry = RoleChangeLog(
                target_id=target_id,
                changed_by_id=changed_by_id,
                guild_id=guild_id,

                role_id=role_id,
                role_name=role_name,
                change_type=action,

                log_time=time_now()
            )

            self.session.add(log_entry)
            self.session.commit()
            log.info(f"Role change logged for {target_id} ({role_name} {action}).")
            return log_entry
        except Exception as e:
            log.error(f"Error logging role change: {e}")
            self.session.rollback()

    def log_name_change(self, target_id: int, changed_by_id: int, guild_id: int, old_name: str, new_name: str) -> NameChangeLog:
        try:
            log_entry = NameChangeLog(
                target_id=target_id,
                changed_by_id=changed_by_id,
                guild_id=guild_id,

                name_before=old_name,
                name_after=new_name,

                log_time=time_now()
            )

            self.session.add(log_entry)
            self.session.commit()
            log.info(f"Name change logged for {target_id} ({old_name} -> {new_name}).")
            return log_entry
        except Exception as e:
            log.error(f"Error logging name change: {e}")
            self.session.rollback()

    def log_timeout(self, target_id: int, changed_by_id: int, guild_id: int, timed_out_until_before: datetime, timed_out_until: datetime):
        ensure_sailor_exists(target_id)
        try:
            log_entry = TimeoutLog(
                target_id=target_id,
                changed_by_id=changed_by_id,
                guild_id=guild_id,

                timed_out_until_before=timed_out_until_before,
                timed_out_until=timed_out_until,

                log_time=time_now()
            )
            self.session.add(log_entry)
            self.session.commit()
            log.info(f"Timeout logged for {target_id} ({timed_out_until_before} -> {timed_out_until}).")
            return log_entry
        except Exception as e:
            log.error(f"Error logging timeout: {e}")
            self.session.rollback()