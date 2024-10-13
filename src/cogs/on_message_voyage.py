from logging import getLogger

import discord, config, asyncio
from discord.ext import commands
from discord import app_commands
from config import VOYAGE_LOGS
from utils.process_voyage_log import Process_Voyage_Log

from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository

# from utils.database_manager import DatabaseManager   # Imports Database Manager from Utilies if needed uncomment it!

log = getLogger(__name__)

class On_Message_Process_voyage(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    # On Message Events  --- These happen passively as events happen on the server

    @commands.Cog.listener()
    async def on_message(self, message):
        voyage_repository = VoyageRepository()
        hosted_repository = HostedRepository()
        sailor_repository = SailorRepository()
        # Voyage Channel Work
        if message.channel.id == int(VOYAGE_LOGS):
            try:
                await Process_Voyage_Log.process_voyage_log(message, voyage_repository, hosted_repository,
                                                            sailor_repository)
                log.info(f"[{message.id}] Voyage log processed.")
            except Exception as e:
                log.error(f"Error processing voyage log: {e}")
            finally:
                voyage_repository.close_session()
                hosted_repository.close_session()
                sailor_repository.close_session()


        


async def setup(bot: commands.Bot):
    await bot.add_cog(On_Message_Process_voyage(bot))  # Classname(bot)
        