from logging import getLogger

import discord
from discord.ext import commands
from utils.process_voyage_log import Process_Voyage_Log

from src.config import VOYAGE_LOGS, GUILD_ID
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.subclass_repository import SubclassRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.utils.discord_utils import alert_engineers
from src.utils.remove_voyage_log import remove_voyage_log_data

#On Message Editing events adjust voyages

log = getLogger(__name__)

class On_Edit_Voyages(commands.Cog):
    # ... your existing code ...

    def __init__(self, bot: commands.Bot) -> None:
            self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        subclass_repository = SubclassRepository()
        hosted_repository = HostedRepository()
        voyage_repository = VoyageRepository()
        if payload.channel_id == VOYAGE_LOGS:
            log_id = payload.message_id

            # Retrieve the edited message
            try:

                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                # If the author of the message is the bot, ignore it
                if message.author == self.bot.user:
                    return
                log.info(f"[{log_id}] [ON_EDIT] Voyage log message edited.")
                # Check if the message has an original hosted entry
                host = hosted_repository.get_host_by_log_id(log_id)

            except discord.NotFound:
                log.info(f"[{log_id}] [ON_EDIT] Voyage log message not found.")
                return
            except Exception as e:
                log.error(f"[{log_id}] [ON_EDIT] Error fetching message information: {e}")
                await alert_engineers(
                            bot=self.bot,
                            message=f"Error fetching message information for voyage log message {log_id}",
                            exception=e
                        )
                return

            try:
                await remove_voyage_log_data(self.bot, log_id, hosted_repository, voyage_repository)
            except Exception as e:
                log.error(f"[{log_id}] [ON_EDIT] Error removing old data: {e}")
                await alert_engineers(
                            bot=self.bot,
                            message=f"Error removing old data for voyage log message {log_id}",
                            exception=e
                        )
                return

            # Process the new message
            try:
                guild = self.bot.get_guild(GUILD_ID)
                logs_channel = guild.get_channel(VOYAGE_LOGS)
                log_message = await logs_channel.fetch_message(int(log_id))
                await Process_Voyage_Log.process_voyage_log(log_message)
                log.info(f"[{log_id}] [ON_EDIT] Voyage log message successfully processed.")
            except Exception as e:
                log.error(f"[{log_id}] [ON_EDIT] Error processing new data: {e}")
                await alert_engineers(
                            bot=self.bot,
                            message=f"Error processing new data for voyage log message {log_id}",
                            exception=e
                        )


        subclass_repository.close_session()
        hosted_repository.close_session()
        voyage_repository.close_session()

async def setup(bot: commands.Bot):
    await bot.add_cog(On_Edit_Voyages(bot))  # Classname(bot)