from logging import getLogger
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands

from src.config import JE_AND_UP
from src.config.main_server import GUILD_ID, VOYAGE_LOGS
from src.config.ranks_roles import SNCO_AND_UP
from src.data.repository.voyage_repository import VoyageRepository
from src.utils.discord_utils import get_best_display_name
from src.utils.embeds import default_embed, error_embed
from src.utils.time_utils import format_time, get_time_difference, get_time_difference_past

log = getLogger(__name__)

class VoyageTogether(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="voyagetogether", description="Statistics on how often two users have voyaged together")
    @app_commands.describe(target_one="Select the user you want to compare against the other user")
    @app_commands.describe(target_two="Select the user you want to compare against the other user (optional)")
    @app_commands.checks.has_any_role(*SNCO_AND_UP)
    async def voyage_together(self, interaction: discord.interactions, target_one: discord.Member, target_two: discord.Member = None):
        await interaction.response.defer(ephemeral=True)

        if target_two is None:
            target_two : discord.Member = interaction.user

        voyage_repository = VoyageRepository()
        voyages = voyage_repository.get_incommon_voyages(target_one.id, target_two.id)
        count = len(voyages)


        generic = default_embed(
            title="Voyage Together",
            description=f"{get_best_display_name(self.bot, target_one.id)} and {get_best_display_name(self.bot, target_two.id)} have voyaged together {count} times.",
        )

        embeds = []
        for i in range(0, len(voyages), 25):
            embed = default_embed(
                title="Voyage Together Logs",
            )
            for voyage in voyages[i:i + 25]:
                embed.add_field(
                    name=f"Voyage: https://discord.com/channels/{GUILD_ID}/{VOYAGE_LOGS}/{voyage.log_id} ({voyage.log_id})",
                    value=f"**Date:** {voyage.log_time.strftime('%Y-%m-%d')} - `{format_time(get_time_difference_past(voyage.log_time))} ago`"
                          f"\n **Host:** <@{voyage.hosted.target_id}>",
                    inline=False
                )
            embeds.append(embed)

        await interaction.followup.send(embed=generic, ephemeral=True)

        for embed in embeds:
            await interaction.followup.send(embed=embed, ephemeral=True)

    @voyage_together.error
    async def voyage_together_error(self, interaction: discord.Interaction, error: commands.CommandError):
        log.error(f"Error occurred in member command: {error}")
        if isinstance(error, app_commands.errors.MissingAnyRole):
            embed = error_embed(
                title="Missing Permissions",
                description="You do not have the required permissions to use this command.",
                footer=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(VoyageTogether(bot))
