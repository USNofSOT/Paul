import discord, config
from discord.ext import commands
from discord import app_commands
# from utils.database_manager import DatabaseManager   # Imports Database Manager from Utilies if needed uncomment it!

class Test(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    
    #Put Command here:
    #
    # ! commands:
    # @commands.command()
    # async def **COMMAND NAME**(self, ctx):
    #
    #Slash Command
    # @app_commands.command(name="", description="")
    # async def _*name*(self, ctx: discord.Interaction):
    #

async def setup(bot: commands.Bot):
    await bot.add_cog(Test(bot))  # Classname(bot)
        