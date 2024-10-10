import discord, config, asyncio
from discord.ext import commands
from discord import app_commands
from config import VOYAGE_LOGS
from utils.process_voyage_log import Process_Voyage_Log

# from utils.database_manager import DatabaseManager   # Imports Database Manager from Utilies if needed uncomment it!

class On_Message_Process_voyage(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    # On Message Events  --- These happen passively as events happen on the server

    @commands.Cog.listener()
    async def on_message(self, message):
        # Voyage Channel Work
        if message.channel.id == int(VOYAGE_LOGS):
            await Process_Voyage_Log.process_voyage_log(message)
            print(f"Voyage log processed: {message.id}")


        


async def setup(bot: commands.Bot):
    await bot.add_cog(On_Message_Process_voyage(bot))  # Classname(bot)
        