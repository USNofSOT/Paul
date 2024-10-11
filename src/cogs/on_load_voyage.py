import discord, config, asyncio
from discord.ext import commands
from discord import app_commands
from config import VOYAGE_LOGS
from utils.process_voyage_log import Process_Voyage_Log

# from utils.database_manager import DatabaseManager   # Imports Database Manager from Utilies if needed uncomment it!

class On_Load_Voyages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        try:
            print(f"{self.bot.user} started procesing logs!")
        
            channel = self.bot.get_channel(VOYAGE_LOGS)
            async for message in channel.history(limit=50, oldest_first=False):  # Fetch the last 50
                await Process_Voyage_Log.process_voyage_log(message)
                await asyncio.sleep(1)  # Introduce a 1second delay to prevent blocking
                #print(f"Processed log: {message.id}.")  #enable this line if you need to view the processing as it happens.
           
        except Exception as e:
            print("An error with processing existing voyage logs has occurred: ", e)


async def setup(bot: commands.Bot):
    await bot.add_cog(On_Load_Voyages(bot))  # Classname(bot)
        