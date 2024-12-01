from logging import getLogger

import discord
from discord.ext import commands

from src.config import VOYAGE_LOGS
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.subclass_repository import SubclassRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.utils.discord_utils import alert_engineers
from src.utils.remove_voyage_log import remove_voyage_log_data

log = getLogger(__name__)

class On_Delete_Voyages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        subclass_repository = SubclassRepository()
        hosted_repository = HostedRepository()
        voyage_repository = VoyageRepository()

        if payload.channel_id == VOYAGE_LOGS:
            log_id = payload.message_id

            # Retrieve the deleted message
            try:

                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                # If the author of the message is the bot, ignore it
                if message.author == self.bot.user:
                    return
                log.info(f"[{log_id}] [ON_DELETE] Voyage log message found.")
            except discord.NotFound:
                log.info(f"[{log_id}] [ON_DELETE] Voyage log message not found.")
            except Exception as e:
                log.error(f"[{log_id}] [ON_DELETE] Error fetching message information: {e}")
                await alert_engineers(
                    bot=self.bot,
                    message=f"Error fetching message information for voyage log message {log_id}",
                    exception=e
                )
                return

            try:
                # Check if the message has an original hosted entry
                host = hosted_repository.get_host_by_log_id(log_id)
            except Exception as e:
                log.error(f"[{log_id}] [ON_DELETE] Error fetching hosted entry: {e}")
                await alert_engineers(
                    bot=self.bot,
                    message=f"Error fetching hosted entry for voyage log message {log_id}",
                    exception=e
                )
                return

            try:
                await remove_voyage_log_data(self.bot, log_id, hosted_repository, voyage_repository, subclass_repository)
            except Exception as e:
                log.error(f"[{log_id}] [ON_DELETE] Error removing old data: {e}")
                await alert_engineers(
                    bot=self.bot,
                    message=f"Error removing data from voyage log message {log_id}",
                    exception=e
                )
                return

        subclass_repository.close_session()
        hosted_repository.close_session()
        voyage_repository.close_session()

async def setup(bot: commands.Bot):
    await bot.add_cog(On_Delete_Voyages(bot))  # Classname(bot)