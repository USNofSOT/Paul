import logging
from typing import Optional

from src.data import CommandCooldownStat
from src.data.repository.common.base_repository import BaseRepository, Session
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)
COMMAND_NAME_MAX_LENGTH = 64


class CommandCooldownStatsRepository(BaseRepository[CommandCooldownStat]):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(CommandCooldownStat, session)

    def _get_or_create_command_cooldown_stat(
            self,
            command_name: str,
    ) -> CommandCooldownStat:
        command_name = command_name[:COMMAND_NAME_MAX_LENGTH]
        command_cooldown_stat = (
            self.session.query(CommandCooldownStat)
            .filter(CommandCooldownStat.command_name == command_name)
            .first()
        )
        if command_cooldown_stat is None:
            command_cooldown_stat = CommandCooldownStat(
                command_name=command_name,
                cooldown_seconds=0,
                trigger_count=0,
                last_retry_after_seconds=0,
            )
        return command_cooldown_stat

    def record_cooldown(
            self,
            command_name: str,
            *,
            cooldown_seconds: int,
            retry_after_seconds: int,
    ) -> CommandCooldownStat:
        try:
            command_name = command_name[:COMMAND_NAME_MAX_LENGTH]
            command_cooldown_stat = self._get_or_create_command_cooldown_stat(
                command_name
            )
            command_cooldown_stat.cooldown_seconds = max(0, cooldown_seconds)
            command_cooldown_stat.trigger_count += 1
            command_cooldown_stat.last_retry_after_seconds = max(
                0,
                retry_after_seconds,
            )
            command_cooldown_stat.last_triggered_at = utc_time_now()

            self.session.add(command_cooldown_stat)
            self.session.commit()
            return command_cooldown_stat
        except Exception as e:
            self.session.rollback()
            log.error(
                "Error recording command cooldown stats for %s: %s",
                command_name,
                e,
            )
            raise e

    def get_command_cooldown_stat(
            self,
            command_name: str,
    ) -> CommandCooldownStat | None:
        try:
            return (
                self.session.query(CommandCooldownStat)
                .filter(CommandCooldownStat.command_name == command_name)
                .first()
            )
        except Exception as e:
            self.session.rollback()
            log.error(
                "Error getting command cooldown stats for %s: %s",
                command_name,
                e,
            )
            raise e

    def clear_all_command_cooldown_stats(self) -> int:
        try:
            deleted_rows = self.session.query(CommandCooldownStat).delete()
            self.session.commit()
            return deleted_rows
        except Exception as e:
            self.session.rollback()
            log.error("Error clearing command cooldown stats: %s", e)
            raise e
