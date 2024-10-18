from dis import disco
from logging import getLogger

from discord.ext import commands

from src.config import NETC_GUILD_ID, JLA_GRADUATE_ROLE, SNLA_GRADUATE_ROLE, SOCS_GRADUATE_ROLE, OCS_GRADUATE_ROLE, \
    GUILD_ID, SPD_GUILD_ID
from src.data.repository.training_records_repository import TrainingRecordsRepository

log = getLogger(__name__)


class OnMemberUpdateNicknameSync(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.guild.id == GUILD_ID:
            origin_guild = self.bot.get_guild(GUILD_ID)
            guilds_to_be_synced = [self.bot.get_guild(NETC_GUILD_ID), self.bot.get_guild(SPD_GUILD_ID)]

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

        log.info(f"[SYNC] Member updated: {before} -> {after}")

async def setup(bot: commands.Bot):
    await bot.add_cog(OnMemberUpdateNicknameSync(bot))