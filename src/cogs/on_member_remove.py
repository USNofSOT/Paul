from discord.ext import commands

from src.config.ranks_roles import E2_AND_UP
from src.data.repository.auditlog_repository import AuditLogRepository
from src.utils.ship_utils import get_ship_role_id_by_member


class OnMemberRemove(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        audit_log_repository = AuditLogRepository()

        member_roles = [role.id for role in member.roles]
        e2_or_above = any(role in member_roles for role in E2_AND_UP)

        audit_log_repository.log_member_removed(member.id, member.guild.id, e2_or_above, get_ship_role_id_by_member(member))

        audit_log_repository.close_session()

async def setup(bot: commands.Bot):
    await bot.add_cog(OnMemberRemove(bot))
