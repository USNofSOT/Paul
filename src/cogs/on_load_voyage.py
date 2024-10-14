from logging import getLogger

import discord, config, asyncio
from discord.ext import commands
from discord import app_commands
from src.config import VOYAGE_LOGS
from sqlalchemy.orm import sessionmaker
from src.utils.process_voyage_log import Process_Voyage_Log

from src.data import engine
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository

# from utils.database_manager import DatabaseManager   # Imports Database Manager from Utilies if needed uncomment it!

log = getLogger(__name__)

class On_Load_Voyages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        voyage_repository = VoyageRepository()
        hosted_repository = HostedRepository()
        sailor_repository = SailorRepository()

        try:
            log.info("Processing existing voyage logs.")


            channel = self.bot.get_channel(VOYAGE_LOGS)
            async for message in channel.history(limit=50, oldest_first=False):  # Fetch the last 50
                await Process_Voyage_Log.process_voyage_log(message, voyage_repository, hosted_repository, sailor_repository)
                await asyncio.sleep(0.5)  # Introduce a 1second delay to prevent blocking
                #print(f"Processed log: {message.id}.")  #enable this line if you need to view the processing as it happens.
        except Exception as e:
            log.error(f"Error processing existing voyage logs: {e}")
        finally:
            log.info("Finished processing existing voyage logs.")
            voyage_repository.close_session()
            hosted_repository.close_session()
            sailor_repository.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(On_Load_Voyages(bot))  # Classname(bot)
        