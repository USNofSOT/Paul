from logging import getLogger

import discord
from discord import AuditLogDiff
from discord.ext import commands

from src.data import RoleChangeType
from src.data.repository.auditlog_repository import AuditLogRepository
from src.data.repository.sailor_repository import ensure_sailor_exists

log = getLogger(__name__)

class OnAuditLogEntryCreate(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if hasattr(entry.target, 'id') and isinstance(entry.target.id, int):
            ensure_sailor_exists(int(entry.target.id))

        # Check if member has been updated
        if entry.action == discord.AuditLogAction.member_update:
            auditlog_repository = AuditLogRepository()
            try:
                log.info(f"[AUDIT LOG] [{entry.id}] Generic member update detected.")

                member_before : AuditLogDiff.member = entry.changes.before
                member_after : AuditLogDiff.member = entry.changes.after

                # If the update was a (nick)name change
                if hasattr(member_before, 'nick') or hasattr(member_after, 'nick') and member_before.nick != member_after.nick:
                    log.info(f"[AUDIT LOG] [{entry.id}] Member name changed.")
                    auditlog_repository.log_name_change(
                        target_id=int(entry.target.id),
                        changed_by_id=entry.user_id,
                        guild_id=entry.guild.id,
                        old_name=member_before.nick or None,
                        new_name=member_after.nick or None
                    )

                # Check if a timeout was added
                if hasattr(member_before, 'timed_out_until') or hasattr(member_after, 'timed_out_until') and member_before.timed_out_until != member_after.timed_out_until:
                    log.info(f"[AUDIT LOG] [{entry.id}] Member timeout changed.")
                    timeout = auditlog_repository.log_timeout(
                        target_id=int(entry.target.id),
                        changed_by_id=entry.user_id,
                        guild_id=entry.guild.id,
                        timed_out_until_before=member_before.timed_out_until,
                        timed_out_until=member_after.timed_out_until
                    )
            except Exception as e:
                log.error(f"[AUDIT LOG] Error logging audit log entry: {e}")
            finally:
                auditlog_repository.close_session()

        if entry.action == discord.AuditLogAction.member_role_update:
            auditlog_repository = AuditLogRepository()
            try:
                log.info(f"[AUDIT LOG] [{entry.id}] Member role update detected.")

                member_before : AuditLogDiff.member = entry.changes.before
                member_after : AuditLogDiff.member = entry.changes.after

                # If the update was a role change
                if member_before.roles != member_after.roles:
                    log.info(f"[AUDIT LOG] [{entry.id}] Member roles changed.")
                    roles_added = [role for role in member_after.roles if role not in member_before.roles]
                    roles_removed = [role for role in member_before.roles if role not in member_after.roles]

                    for role in roles_added:
                        log.info(f"[AUDIT LOG] [{entry.id}] Role added: {role.name}")
                        auditlog_repository.log_role_change(
                            target_id=int(entry.target.id),
                            changed_by_id=entry.user_id,
                            guild_id=entry.guild.id,
                            role_id=role.id,
                            role_name=role.name,
                            action=RoleChangeType.ADDED
                        )
                    for role in roles_removed:
                        log.info(f"[AUDIT LOG] [{entry.id}] Role removed: {role.name}")
                        auditlog_repository.log_role_change(
                            target_id=int(entry.target.id),
                            changed_by_id=entry.user_id,
                            guild_id=entry.guild.id,
                            role_id=role.id,
                            role_name=role.name,
                            action=RoleChangeType.REMOVED
                        )
            except Exception as e:
                log.error(f"[AUDIT LOG] Error logging audit log entry: {e}")
            finally:
                auditlog_repository.close_session()



async def setup(bot: commands.Bot):
    await bot.add_cog(OnAuditLogEntryCreate(bot))