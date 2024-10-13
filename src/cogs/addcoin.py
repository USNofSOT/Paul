import discord
from discord.ext import commands
from discord import app_commands

from src.config import JO_AND_UP
from src.data.repository.coin_repository import CoinRepository
from logging import getLogger

log = getLogger(__name__)


class AddCoin(commands.Cog):
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

    @app_commands.command(name="addcoin", description="Add coins to a user")
    @app_commands.describe(target="Select the user you want to add coins to")
    @app_commands.checks.has_any_role(JO_AND_UP)
    async def addcoin(self, interaction: discord.Interaction, target: discord.Member = None, coins: int = 0):
        # Set the target to the user running the command if not provided
        if target is None:
            target = interaction.user

        coin_repo = CoinRepository()
        coin_repo.add_coins(target.id, coins)
        await interaction.response.send_message(f"Added {coins} coins to {target.display_name or target.name}")


async def setup(bot: commands.Bot):
    await bot.add_cog(AddCoin(bot))
