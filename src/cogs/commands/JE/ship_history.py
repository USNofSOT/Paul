import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import GUILD_ID, VOYAGE_LOGS
from config.emojis import ANCIENT_COINS_EMOJI, DOUBLOONS_EMOJI, GOLD_EMOJI
from src.config.ranks_roles import JE_AND_UP
from utils.embeds import error_embed
from utils.hosted_utils import ShipHistory, get_ship_names
from utils.ship_utils import convert_to_ordinal

log = logging.getLogger(__name__)


async def autocomplete_ship(
    interaction: discord.Interaction, current_input: str
) -> list[app_commands.Choice]:
    ship_names: list[str] = get_ship_names(
        get_main_ship_names=True, get_auxiliary_ship_names=True
    )
    choices = []
    for ship in ship_names:
        ship_name = ship.replace("USS ", "")
        if (
            current_input == ""
            or ship.lower().startswith(current_input.lower())
            or ship_name.lower().startswith(current_input.lower())
        ):
            choices.append(app_commands.Choice(name=ship, value=ship))
    return choices[:25]


class ShipHistoryCommand(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="ship_history",
        description="Get information about the ships you or a user has hosted",
    )
    @app_commands.autocomplete(ship=autocomplete_ship)
    @app_commands.describe(ship="Select the ship you want to get information about")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def ship_history(self, interaction: discord.interactions, ship: str):
        await interaction.response.defer(ephemeral=False)
        if ship is None:
            await interaction.followup.send(
                embed=error_embed(
                    "This ship does not exist.", "Please select a valid ship."
                )
            )
            return
        if ship not in get_ship_names(
            get_main_ship_names=True, get_auxiliary_ship_names=True
        ):
            await interaction.followup.send(
                embed=error_embed(
                    "This ship does not exist.", "Please select a valid ship."
                )
            )
            return

        try:
            history: ShipHistory = ShipHistory(ship)
        except ValueError:
            await interaction.followup.send(
                embed=error_embed(
                    "This ship does not have a history.",
                    "Please select a different ship.",
                )
            )

        embed = discord.Embed(
            title=f"{ship}",
            description=f"The ship history of the {ship}",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="Voyage Count",
            value=f"{convert_to_ordinal(history.voyage_count)}",
            inline=True,
        )
        embed.add_field(
            name="Gold",
            value=f"{GOLD_EMOJI} {history.total_gold_earned:,}",
            inline=True,
        )
        embed.add_field(
            name="Doubloons",
            value=f"{DOUBLOONS_EMOJI} {history.total_doubloons_earned:,}",
            inline=True,
        )

        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(
            name="Ancient Coins",
            value=f"{ANCIENT_COINS_EMOJI} {history.total_ancient_coins_earned:,}",
            inline=True,
        )
        embed.add_field(
            name="Fish Caught",
            value=f":fish: {history.total_fishes_caught:,}",
            inline=True,
        )

        if history.get_top_three_hosts():
            embed.add_field(
                name=":trophy:  Top 3 Hosts",
                value="\n".join(
                    [
                        f"{
                            self.bot.get_user(host.target_id).mention
                            if self.bot.get_user(host.target_id)
                            else 'Unknown'
                        } "
                        f"- {host.total_voyages} "
                        for host in history.get_top_three_hosts()
                    ]
                ),
                inline=True,
            )
        top_three_voyage_types = history.get_top_three_voyage_types(ignore_unknown=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        if top_three_voyage_types:
            embed.add_field(
                name=":sailboat:  Top 3 Voyage Types",
                value="\n".join(
                    [
                        f"{voyage.voyage_type.name.capitalize()} "
                        f"- {voyage.total_voyages} "
                        for voyage in top_three_voyage_types
                    ]
                ),
                inline=True,
            )

        if not history.history:
            embed.add_field(
                name=":stopwatch: Recent Voyages",
                value="No voyages have been hosted on this ship.",
            )
        else:
            most_recent_voyages = history.history[-3:]
            most_recent_voyages = most_recent_voyages[::-1]
            embed.add_field(
                name=":stopwatch:  Recent Voyages",
                value="\n".join(
                    [
                        f""
                        f"https://discord.com/channels/"
                        f"{GUILD_ID}/{VOYAGE_LOGS}/{voyage.log_id} "
                        f"<t:{int(voyage.log_time.timestamp())}:R> "
                        f"- <@{voyage.target_id}>"
                        f""
                        for voyage in most_recent_voyages
                    ]
                ),
                inline=False,
            )

        embed.set_footer(
            text="Only voyages with correct specifications "
            "are counted (starting from 2025-02-01)"
        )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ShipHistoryCommand(bot))
