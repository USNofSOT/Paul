from dis import disco
from logging import getLogger

from discord.ext import commands

from src.config.main_server import GUILD_ID
from src.config.netc_server import NETC_GUILD_ID
from src.config.spd_servers import SPD_GUILD_ID
from src.data.repository.training_records_repository import TrainingRecordsRepository

log = getLogger(__name__)


class OnMemberUpdateNicknameSync(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        IGNORE_USERS = [1304027374421020693]

        if after.guild.id == GUILD_ID:
            origin_guild = self.bot.get_guild(GUILD_ID)
            guilds_to_be_synced = [self.bot.get_guild(NETC_GUILD_ID), self.bot.get_guild(SPD_GUILD_ID)]
            if before.id not in IGNORE_USERS:
                if before.nick != after.nick:
                    log.info(f"[SYNC] Nickname changed in {origin_guild.name}, from {before.nick} to {after.nick}")
                    for guild in guilds_to_be_synced:
                        member = guild.get_member(after.id)
                        if member:
                            if member.nick != after.nick:
                                log.info(f"[SYNC] Updating nickname for {member} in {guild.name}")
                                await member.edit(nick=after.nick)
                            else:
                                log.info(f"[SYNC] Nickname already in sync for {member} in {guild.name}")
                        else:
                            log.info(f"[SYNC] Member not found in {guild.name}")

async def setup(bot: commands.Bot):
    await bot.add_cog(OnMemberUpdateNicknameSync(bot))