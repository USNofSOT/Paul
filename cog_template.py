import discord
from discord.ext import commands
from discord import app_commands
# from src.data.repository.subclass_repository import SubclassRepository
from logging import getLogger

log = getLogger(__name__)


class Test(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Example of repository usage
        # self.subclass_repository = SubclassRepository()

    #Put Command here:
    #
    # ! commands:
    # @commands.command()
    # async def **COMMAND NAME**(self, ctx):
    #
    #Slash Command
    # @app_commands.command(name="", description="")
    # async def _*name*(self, interaction: discord.Interaction):
    #


async def setup(bot: commands.Bot):
    await bot.add_cog(Test(bot))
