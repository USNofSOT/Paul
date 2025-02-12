from logging import getLogger
from typing import Type

import discord
from config import GUILD_ID, VOYAGE_LOGS
from config.emojis import ANCIENT_COINS_EMOJI, DOUBLOONS_EMOJI, GOLD_EMOJI
from config.ships import SHIPS
from data import Hosted
from data.repository.hosted_repository import HostedRepository
from discord import app_commands
from discord.ext import commands
from utils.ship_utils import (
    convert_to_ordinal,
    get_ships_mapped,
    list_auxiliary_ships,
    list_main_ships,
)

from src.config import JE_AND_UP
from src.utils.embeds import default_embed, error_embed

log = getLogger(__name__)


async def is_valid_main_ship(main_ship: str) -> bool:
    return main_ship in list_main_ships()


async def is_valid_auxiliary_ship(auxiliary_ship: str) -> bool:
    return auxiliary_ship in list_auxiliary_ships()


async def is_aux_part_of_main_ship(main_ship: str, auxiliary_ship: str) -> bool or list[str]:
    ship_map = get_ships_mapped()
    if auxiliary_ship in ship_map.get(main_ship, []):
        return True
    ships_with_aux = [ship for ship, aux_list in ship_map.items() if auxiliary_ship in aux_list]
    return ships_with_aux if ships_with_aux else False


async def autocomplete_ship(current_input: str, list_ships_func) -> list[app_commands.Choice]:
    ships = list_ships_func()
    choices = []
    for ship in ships:
        ship_name = ship.replace("USS ", "")
        if current_input == "":
            choices.append(app_commands.Choice(name=ship, value=ship))
        elif ship.lower().startswith(current_input.lower()) or ship_name.lower().startswith(
            current_input.lower()
        ):
            choices.append(app_commands.Choice(name=ship, value=ship))
    return choices[:25]


async def autocomplete_auxiliary_ship(
    interaction: discord.Interaction, current_input: str
) -> list[app_commands.Choice]:
    return await autocomplete_ship(current_input, list_auxiliary_ships)


async def autocomplete_main_ship(
    interaction: discord.Interaction, current_input: str
) -> list[app_commands.Choice]:
    return await autocomplete_ship(current_input, list_main_ships)


async def build_embed(hosted: Type[Hosted], total_hosted: int, current_index: int) -> discord.Embed:
    ship_emoji = None
    for ship in SHIPS:
        if ship.name == hosted.ship_name:
            ship_emoji = ship.emoji
            break

    embed = default_embed(
        title="Voyage Log Information",
        description=f"https://discord.com/channels/"
        f"{GUILD_ID}/{VOYAGE_LOGS}/{hosted.log_id} "
        f"by <@{hosted.target_id}>",
    )
    embed.set_footer(text=f"Showing {current_index}/{total_hosted} found logs")

    if ship_emoji:
        embed.add_field(
            name="Ship",
            value=f"{ship_emoji} {hosted.ship_name if hosted.ship_name else 'N/A'}",
            inline=True,
        )
    else:
        embed.add_field(
            name="Ship",
            value=hosted.ship_name if hosted.ship_name else "N/A",
            inline=True,
        )

    embed.add_field(
        name="Auxiliary Ship",
        value=hosted.auxiliary_ship_name if hosted.auxiliary_ship_name else "N/A",
        inline=True,
    )
    embed.add_field(
        name="Voyage Count",
        value=convert_to_ordinal(hosted.ship_voyage_count) if hosted.ship_voyage_count else "N/A",
        inline=True,
    )

    embed.add_field(
        name="Voyage Type",
        value=hosted.voyage_type.name.capitalize() if hosted.voyage_type else "N/A",
        inline=True,
    )
    embed.add_field(name="Gold", value=f"{GOLD_EMOJI} {hosted.gold_count:,}", inline=True)
    embed.add_field(
        name="Doubloons",
        value=f"{DOUBLOONS_EMOJI} {hosted.doubloon_count:,}",
        inline=True,
    )

    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(
        name="Ancient Coins",
        value=f"{ANCIENT_COINS_EMOJI} {hosted.ancient_coin_count:,}"
        if hosted.ancient_coin_count
        else "N/A",
        inline=True,
    )
    embed.add_field(
        name="Fish",
        value=f":fish: {hosted.fish_count:,}" if hosted.fish_count else "N/A",
        inline=True,
    )

    return embed


class LogBookView(discord.ui.View):
    def __init__(self, bot, hosted: [Hosted]):
        super().__init__()
        self.bot = bot
        self.hosted: [Hosted] = hosted
        self.selected_index = 0

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⬅️")
    async def on_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_index += 1
        if self.selected_index >= len(self.hosted):
            self.selected_index = 0
        # Update the original message
        embed = await build_embed(
            self.hosted[self.selected_index],
            len(self.hosted),
            len(self.hosted) - self.selected_index,
        )
        await interaction.message.edit(embed=embed, view=self)
        # Acknowledge the interaction
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔄")
    async def on_refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update the original message
        embed = await build_embed(
            self.hosted[self.selected_index],
            len(self.hosted),
            len(self.hosted) - self.selected_index,
        )
        await interaction.message.edit(embed=embed, view=self)
        # Acknowledge the interaction
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="➡️")
    async def on_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selected_index -= 1
        if self.selected_index < 0:
            self.selected_index = len(self.hosted) - 1
        # Update the original message
        embed = await build_embed(
            self.hosted[self.selected_index],
            len(self.hosted),
            len(self.hosted) - self.selected_index,
        )
        await interaction.message.edit(embed=embed, view=self)
        # Acknowledge the interaction
        await interaction.response.defer()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)


class Logbook(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="logbook", description="Get information about a member")
    @app_commands.autocomplete(main_ship=autocomplete_main_ship)
    @app_commands.autocomplete(auxiliary_ship=autocomplete_auxiliary_ship)
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def logbook(
        self,
        interaction: discord.interactions,
        main_ship: str = None,
        auxiliary_ship: str = None,
    ):
        if main_ship and not await is_valid_main_ship(main_ship):
            embed = error_embed(
                title="Logbook Information", description="Invalid main ship provided."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if auxiliary_ship and not await is_valid_auxiliary_ship(auxiliary_ship):
            embed = error_embed(
                title="Logbook Information",
                description="Invalid auxiliary ship provided.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if auxiliary_ship and main_ship:
            check_relation = await is_aux_part_of_main_ship(main_ship, auxiliary_ship)
            # If false, then auxiliary ship is not part of main ship
            if not check_relation:
                embed = error_embed(
                    title="Logbook Information",
                    description=f"{auxiliary_ship} is not part of {main_ship}.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if isinstance(check_relation, list):
                embed = error_embed(
                    title="Logbook Information",
                    description=f"{auxiliary_ship} is part of one or more main ships:"
                    f" {', '.join(check_relation)}. Please specify the correct main ship.",
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        hosted_repository = HostedRepository()
        hosted = hosted_repository.get_hosted_by_either_ship_name_or_auxiliary_ship_name(
            main_ship, auxiliary_ship, None
        )
        if not hosted:
            embed = error_embed(
                title="Logbook Information",
                description="No information found for the provided ship name. "
                "We might've not recorded this ship yet.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = await build_embed(hosted[0], len(hosted), len(hosted))
        view = LogBookView(self.bot, hosted)

        await interaction.response.send_message(embed=embed, view=view)

        hosted_repository.close_session()

    @logbook.error
    async def logbook_error(self, interaction: discord.Interaction, error: commands.CommandError):
        log.error("Error occurred in logbook command")
        if isinstance(error, app_commands.errors.MissingAnyRole):
            embed = error_embed(
                title="Missing Permissions",
                description="You do not have the required permissions to use this command.",
                footer=False,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = error_embed(exception=error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Logbook(bot))
