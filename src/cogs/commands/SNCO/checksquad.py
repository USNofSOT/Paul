import discord
from discord.ext import commands
from discord import app_commands, Embed

from src.config.ranks_roles import NRC_ROLE, SNCO_AND_UP
from src.data import Sailor
from src.data.repository.sailor_repository import SailorRepository
from src.utils.embeds import error_embed, default_embed

#  This command is used to check if sailors have a squad role assigned if they are on a ship.
#  The command checkes all members in the ship role to see if they have a role with Squad in the name, or have the CoS, FO, or CO roles.
#  The command then displays the ship command structure for the user, with sailors not in the structure listed at the bottom.

class CheckSquad(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.command(name="checksquad", description="Check Sailors have a squad role on your ship")
    @app_commands.describe(target="Select the Ship you want to check")
    async def checksquad(self, interaction: discord.interactions, target: discord.Role):
        await interaction.response.defer (ephemeral=True)


    
async def setup(bot: commands.Bot):
    await bot.add_cog(CheckSquad(bot))  # Classname(bot)
