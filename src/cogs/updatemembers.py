import discord, asyncio
from discord.ext import commands
from discord import app_commands
from src.data.repository.sailor_repository import SailorRepository
from logging import getLogger
from config import BOA_ROLE, NSC_ROLE
log = getLogger(__name__)


class UpdateMembers(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.sailor_repository = SailorRepository()

    @app_commands.command(name="updatemembers", description="Update the Sailorinfo table with current server members")
    @commands.has_any_role(NSC_ROLE)
    async def updatemembers(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # Defer the response for potentially long operation

        try:
            guild_id = interaction.guild.id  # Get the server ID
            guild = interaction.guild  # Get the server object
            member_count = 0

            for member in guild.members:
                await asyncio.sleep(.1)  # Introduce a .1second delay to prevent blocking
                if not SailorRepository.discord_id_exists(member.id):
                    SailorRepository.add_discord_id(member.id)
                    member_count += 1

            await interaction.followup.send(f"Updated Sailorinfo with {member_count} new members.")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(UpdateMembers(bot))
