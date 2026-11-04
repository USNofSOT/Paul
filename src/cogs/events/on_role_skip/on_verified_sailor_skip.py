"""Warn when Recruit is assigned before Verified Sailor."""

from datetime import datetime
from logging import getLogger

import discord
from discord.ext import commands

from src.config.main_server import GUILD_ID, BOA_Alert
from src.config.ranks_roles import E1_ROLES, E2_ROLES, VERIFIED_ROLE, BOA_ROLE
from src.data.repository.auditlog_repository import AuditLogRepository

log = getLogger(__name__)
SEAMAN_ROLE_ID = E2_ROLES[0]

class OnVerifiedSailorSkip(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry) -> None:
        """Warn when Recruit is granted before Verified Sailor."""
        if (
            entry.guild.id != GUILD_ID
            or entry.action != discord.AuditLogAction.member_role_update
        ):
            return

        alert_channel = entry.guild.get_channel(BOA_Alert)

        target = entry.target
        target_id = getattr(target, "id", None)
        if target_id is None or getattr(target, "bot", False):
            return

        before_roles = getattr(entry.changes.before, "roles", [])
        after_roles = getattr(entry.changes.after, "roles", [])
        before_role_ids = {role.id for role in before_roles}
        after_role_ids = {role.id for role in after_roles}
        recruit_role_added = any(
            role_id in after_role_ids and role_id not in before_role_ids
            for role_id in E1_ROLES
        )
        seaman_role_added = (
            SEAMAN_ROLE_ID in after_role_ids
            and SEAMAN_ROLE_ID not in before_role_ids
        )
        recruit_role_still_assigned = any(
            role_id in after_role_ids for role_id in E1_ROLES
        )

        recruit_before_verified = (
            recruit_role_added and VERIFIED_ROLE not in after_role_ids
        )
        warnings = []
        if recruit_before_verified:
            warnings.append(
                "The **Recruit** role was assigned before the **Verified Sailor** role"
            )

        has_recruit_role_history = False
        if seaman_role_added:
            member = entry.guild.get_member(target_id)
            if member is None:
                try:
                    member = await entry.guild.fetch_member(target_id)
                except discord.HTTPException:
                    log.warning(
                        "Could not look up member %s for Recruit role history check.",
                        target_id,
                    )

            if member and member.joined_at:
                has_recruit_role_history = self._has_recruit_role_history_since(
                    target_id,
                    member.joined_at,
                )

        if seaman_role_added and recruit_role_still_assigned:
            warnings.append(
                "the **Seaman** role was assigned while the **Recruit** role is still present"
            )
        elif seaman_role_added and not has_recruit_role_history:
            warnings.append(
                "The **Seaman** role was assigned without a Recruit-role assignment "
                "in their current time-in-service."
            )

        if not warnings:
            return

        actor_mention = entry.user.mention if entry.user else "Unknown user"
        target_mention = getattr(target, "mention", f"<@{target_id}>")
        BOA_mention = f"<@&{BOA_ROLE}>"

        if recruit_before_verified and len(warnings) == 1:
            embed = discord.Embed(
                title="⚠️ Verification Warning",
                description=(
                    f"{actor_mention} gave {target_mention} the **Recruit** role before "
                    "the **Verified Sailor** role."
                ),
                color=discord.Color.orange(),
            )
        else:
            embed = discord.Embed(
                title="⚠️ Role Assignment Warning",
                description=(
                    f"{actor_mention} gave {target_mention} a role that requires review:\n"
                    + "\n".join(f"• {warning}" for warning in warnings)
                ),
                color=discord.Color.orange(),
            )
        mentions = [target_mention]
        if entry.user:
            mentions.insert(0, actor_mention)

        await alert_channel.send(
            content=f"{BOA_mention}\n{' '.join(mentions)}",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=True,
                everyone=False,
            ),
        )

    @staticmethod
    def _has_recruit_role_history_since(member_id: int, joined_at: datetime) -> bool:
        """Return whether Recruit changed during the sailor's current membership."""
        repository = AuditLogRepository()
        try:
            for recruit_role_id in E1_ROLES:
                if repository.has_role_change_since(
                    member_id,
                    recruit_role_id,
                    joined_at,
                ):
                    return True
        except Exception:
            log.exception(
                "Could not check Recruit role history for %s since their current join.",
                member_id,
            )
        finally:
            repository.close_session()

        return False


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OnVerifiedSailorSkip(bot))
