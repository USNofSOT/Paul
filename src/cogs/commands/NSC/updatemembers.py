from logging import getLogger

import asyncio
import discord
from config import BOA_ROLE, NSC_ROLE
from discord import app_commands
from discord.ext import commands

from src.data.repository.sailor_repository import SailorRepository
from src.security import require_any_role, audit_interaction, Role

log = getLogger(__name__)


class UpdateMembers(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.sailor_repository = SailorRepository()

    @app_commands.command(name="updatemembers", description="Update the Sailorinfo table with current server members")
    @require_any_role(Role.NSC_OPERATOR)
    @audit_interaction
    async def updatemembers(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # Defer the response for potentially long operation

        try:
            guild_id = interaction.guild.id  # Get the server ID
            guild = interaction.guild  # Get the server object
            member_count = 0

            for member in guild.members:
                await asyncio.sleep(.1)  # Introduce a .1second delay to prevent blocking
                if not self.sailor_repository.check_discord_id_exists(member.id):
                    self.sailor_repository.update_or_create_sailor_by_discord_id(member.id)
                    member_count += 1

            await interaction.followup.send(f"Updated Sailorinfo with {member_count} new members.")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(UpdateMembers(bot))
