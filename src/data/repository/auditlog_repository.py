import datetime
import logging
from typing import Type

from sqlalchemy.orm import sessionmaker

from src.data import NameChangeLog, AuditLog, RoleChangeLog, RoleChangeType, TimeoutLog, BotInteractionType, \
    BotInteractionLog, LeaveChangeLog, BanChangeLog
from src.data.engine import engine
from src.data.repository.sailor_repository import ensure_sailor_exists
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

class AuditLogRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def get_bans_changes_for_e2_or_above_and_between_dates(self, start_date: datetime, end_date: datetime) -> [BanChangeLog]:
        try:
            return self.session.query(BanChangeLog).filter(BanChangeLog.log_time >= start_date, BanChangeLog.log_time <= end_date).all()
        except Exception as e:
            log.error(f"Error getting ban changes for E2 or above and between dates: {e}")
            raise e

    def get_leave_changes_for_e2_or_above_and_between_dates(self, e2_or_above: bool, start_date: datetime, end_date: datetime) -> [LeaveChangeLog]:
        try:
            return self.session.query(LeaveChangeLog).filter(LeaveChangeLog.e2_or_above == e2_or_above, LeaveChangeLog.log_time >= start_date, LeaveChangeLog.log_time <= end_date).all()
        except Exception as e:
            log.error(f"Error getting leave changes for E2 or above and between dates: {e}")
            raise e

    def get_role_changes_for_role_and_action_between_dates(self, role_id: int, action: RoleChangeType, start_date: datetime, end_date: datetime) -> [RoleChangeLog]:
        try:
            return self.session.query(RoleChangeLog).filter(RoleChangeLog.role_id == role_id, RoleChangeLog.change_type == action, RoleChangeLog.log_time >= start_date, RoleChangeLog.log_time <= end_date).all()
        except Exception as e:
            log.error(f"Error getting role changes for role and action between dates: {e}")
            raise e

    def get_latest_role_log_for_target_and_role(self, target_id: int, role_id: int) -> Type[RoleChangeLog] | None:
        try:
            return self.session.query(RoleChangeLog).filter(RoleChangeLog.target_id == target_id, RoleChangeLog.role_id == role_id).order_by(RoleChangeLog.log_time.desc()).first()
        except Exception as e:
            log.error(f"Error getting latest role log for target and role: {e}")
            raise e

    def get_timeout_logs(self, target_id: int = None, limit: int = 10) -> [TimeoutLog]:
        if target_id:
            return self.session.query(TimeoutLog).filter(TimeoutLog.target_id == target_id).order_by(TimeoutLog.log_time.desc()).limit(limit).all()
        else:
            return self.session.query(TimeoutLog).order_by(TimeoutLog.log_time.desc()).limit(limit).all()

    def get_name_changes_logs(self, target_id: int = None, limit: int = 10, guild_id: int = None) -> [NameChangeLog]:
        if target_id and guild_id:
            return self.session.query(NameChangeLog).filter(NameChangeLog.target_id == target_id,NameChangeLog.guild_id == guild_id).order_by(NameChangeLog.log_time.desc()).limit(limit).all()
        elif target_id:
            return self.session.query(NameChangeLog).filter(NameChangeLog.target_id == target_id).order_by(NameChangeLog.log_time.desc()).limit(limit).all()
        elif guild_id:
            return self.session.query(NameChangeLog).filter(NameChangeLog.guild_id == guild_id).order_by(NameChangeLog.log_time.desc()).limit(limit).all()
        else:
            return self.session.query(NameChangeLog).order_by(NameChangeLog.log_time.desc()).limit(limit).all()

    def get_role_changes_logs(self, target_id: int = None, limit: int = 10) -> [RoleChangeLog]:
        if target_id:
            return self.session.query(RoleChangeLog).filter(RoleChangeLog.target_id == target_id).order_by(RoleChangeLog.log_time.desc()).limit(limit).all()
        else:
            return self.session.query(RoleChangeLog).order_by(RoleChangeLog.log_time.desc()).limit(limit).all()

    def log_ban(self, target_id: int, changed_by_id: int, guild_id: int, reason: str = "No reason provided.") -> BanChangeLog:
        try:
            log_entry = BanChangeLog(
                target_id=target_id,
                changed_by_id=changed_by_id,
                guild_id=guild_id,
                reason=reason,
                log_time=utc_time_now()
            )

            self.session.add(log_entry)
            self.session.commit()
            log.info(f"Member banned logged for {target_id}.")
            return log_entry
        except Exception as e:
            log.error(f"Error logging member banned: {e}")
            self.session.rollback()

    def log_member_removed(self, target_id: int, guild_id: int, e2_or_above: bool = False, ship_id: int = None) -> LeaveChangeLog:
        try:
            log_entry = LeaveChangeLog(
                target_id=target_id,
                guild_id=guild_id,
                e2_or_above=e2_or_above,
                ship_role_id=ship_id,
                log_time=utc_time_now()
            )

            self.session.add(log_entry)
            self.session.commit()
            log.info(f"Member removed logged for {target_id}.")
            return log_entry
        except Exception as e:
            log.error(f"Error logging member removed: {e}")
            self.session.rollback()

    def log_role_change(self, target_id: int, changed_by_id: int, guild_id: int, role_id: int, role_name: str, action: RoleChangeType) -> RoleChangeLog:
        try:
            log_entry = RoleChangeLog(
                target_id=target_id,
                changed_by_id=changed_by_id,
                guild_id=guild_id,

                role_id=role_id,
                role_name=role_name,
                change_type=action,

                log_time=utc_time_now()
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

                log_time=utc_time_now()
            )

            self.session.add(log_entry)
            self.session.commit()
            log.info(f"Name change logged for {target_id} ({old_name} -> {new_name}).")
            return log_entry
        except Exception as e:
            log.error(f"Error logging name change: {e}")
            self.session.rollback()

    def log_interaction(self, interaction_type: BotInteractionType, guild_id: int, channel_id: int, user_id: int, command_name: str, failed: bool = False) -> BotInteractionLog:
        try:
            log_entry = BotInteractionLog(
                interaction_type=interaction_type,
                guild_id=guild_id,
                channel_id=channel_id,
                target_id=user_id,
                command_name=command_name,
                failed=failed,
                log_time=utc_time_now()
            )

            self.session.add(log_entry)
            self.session.commit()
            log.info(f"Interaction logged for {user_id} ({command_name}).")
            return log_entry
        except Exception as e:
            log.error(f"Error logging interaction: {e}")
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

                log_time=utc_time_now()
            )
            self.session.add(log_entry)
            self.session.commit()
            log.info(f"Timeout logged for {target_id} ({timed_out_until_before} -> {timed_out_until}).")
            return log_entry
        except Exception as e:
            log.error(f"Error logging timeout: {e}")
            self.session.rollback()