from logging import getLogger

import discord
from discord.ext import commands

from src.data import RoleChangeType
from src.data.repository.auditlog_repository import AuditLogRepository

log = getLogger(__name__)

class OnAuditLogEntryCreate(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):

        # Check if member has been updated
        if entry.action == discord.AuditLogAction.member_update:
            auditlog_repository = AuditLogRepository()
            try:
                log.info(f"[AUDIT LOG] [{entry.id}] Generic member update detected.")

                member_before = entry.changes.before
                member_after = entry.changes.after
                # If the update was a (nick)name change
                if member_before.nick != member_after.nick:
                    log.info(f"[AUDIT LOG] [{entry.id}] Member name changed.")
                    auditlog_repository.log_name_change(
                        target_id=int(entry.target.id),
                        changed_by_id=entry.user_id,
                        guild_id=entry.guild.id,
                        old_name=member_before.nick,
                        new_name=member_after.nick
                    )
            except Exception as e:
                log.error(f"[AUDIT LOG] Error logging audit log entry: {e}")
            finally:
                auditlog_repository.close_session()

        if entry.action == discord.AuditLogAction.member_role_update:
            auditlog_repository = AuditLogRepository()
            try:
                log.info(f"[AUDIT LOG] [{entry.id}] Member role update detected.")

                member_before = entry.changes.before
                member_after = entry.changes.after
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