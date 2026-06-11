from logging import getLogger

from discord.ext import commands, tasks

from src.config.main_server import GUILD_ID, ENVIRONMENT
from src.config.task_timing import DISCORD_MEMBER_SYNC_TASK_INTERVAL_HOURS
from src.data.repository.sailor_repository import SailorRepository

log = getLogger(__name__)


class SyncDiscordMembers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sync_discord_members.start()

    def cog_unload(self):
        self.sync_discord_members.cancel()

    @tasks.loop(hours=DISCORD_MEMBER_SYNC_TASK_INTERVAL_HOURS)
    async def sync_discord_members(self):

        if ENVIRONMENT != "PROD":
            log.info("Not In Production")
            return

        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            log.error("Could not find guild for syncing discord members.")
            return

        repo = SailorRepository()
        try:
            await guild.chunk()

            profiles = [
                {
                    "discord_id": member.id,
                    "nickname": member.nick,
                    "global_name": member.global_name,
                    "discord_name": member.name,
                    "avatar_url": member.display_avatar.url if member.display_avatar else None,
                }
                for member in guild.members
                if not member.bot
            ]

            updated = repo.update_discord_profiles_batch(profiles)
            log.info(
                "Synced Discord profiles for %d/%d guild members.",
                updated,
                len(profiles),
            )
        except Exception as e:
            log.error(
                "Error during Discord member sync: %s",
                e,
                extra={"notify_engineer": True},
            )
        finally:
            repo.close_session()

    @sync_discord_members.before_loop
    async def before_sync(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(SyncDiscordMembers(bot))
