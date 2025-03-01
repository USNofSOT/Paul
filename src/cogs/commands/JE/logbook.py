from logging import getLogger
from typing import List, Type

import discord
from config import GUILD_ID, VOYAGE_LOGS
from config.emojis import ANCIENT_COINS_EMOJI, DOUBLOONS_EMOJI, GOLD_EMOJI
from config.ships import SHIPS
from data import Hosted, VoyageType
from data.repository.hosted_repository import HostedRepository
from discord import Message, app_commands
from discord.ext import commands
from utils.hosted_utils import get_ship_names
from utils.ship_utils import (
    convert_to_ordinal,
)

from src.config import JE_AND_UP
from src.utils.embeds import default_embed, error_embed

log = getLogger(__name__)


async def is_valid_main_ship(main_ship: str) -> bool:
    return main_ship in get_ship_names(
        get_main_ship_names=True,
        get_auxiliary_ship_names=False,
    )


async def is_valid_auxiliary_ship(auxiliary_ship: str) -> bool:
    return auxiliary_ship in get_ship_names(
        get_main_ship_names=False,
        get_auxiliary_ship_names=True,
    )


async def is_aux_part_of_main_ship(main_ship: str, auxiliary_ship: str) -> bool or list[str]:
    ship_map = get_ship_names(
        get_main_ship_names=True,
        get_auxiliary_ship_names=True,
        map_by_main_ship_name=True,
    )
    if auxiliary_ship in ship_map.get(main_ship, []):
        return True
    ships_with_aux = [ship for ship, aux_list in ship_map.items() if auxiliary_ship in aux_list]
    return ships_with_aux if ships_with_aux else False


async def autocomplete_ship(current_input: str, list_ships_func) -> list[app_commands.Choice]:
    ship_names: List[str] = list_ships_func()
    choices = []
    for ship in ship_names:
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
    ship_names = get_ship_names(
        get_main_ship_names=False,
        get_auxiliary_ship_names=True,
    )
    return await autocomplete_ship(current_input, lambda: ship_names)


async def autocomplete_main_ship(
    interaction: discord.Interaction, current_input: str
) -> list[app_commands.Choice]:
    ship_names = get_ship_names(
        get_main_ship_names=True,
        get_auxiliary_ship_names=False,
    )
    return await autocomplete_ship(current_input, lambda: ship_names)


async def build_embed(
    bot, hosted: Type[Hosted], total_hosted: int, current_index: int
) -> discord.Embed:
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

    if hosted.auxiliary_ship_name:
        embed.add_field(
            name="Auxiliary Ship",
            value=hosted.auxiliary_ship_name if hosted.auxiliary_ship_name else "N/A",
            inline=True,
        )
    else:
        embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(
        name="Voyage Count",
        value=convert_to_ordinal(hosted.ship_voyage_count) if hosted.ship_voyage_count else "N/A",
        inline=True,
    )

    voyage_type_emoji = ":question: "
    if hosted.voyage_type.name == VoyageType.PATROL.name:
        voyage_type_emoji = ":sailboat: "
    elif hosted.voyage_type.name == VoyageType.SKIRMISH.name:
        voyage_type_emoji = ":crossed_swords: "
    elif hosted.voyage_type.name == VoyageType.ADVENTURE.name:
        voyage_type_emoji = ":compass: "

    embed.add_field(
        name="Voyage Type",
        value=f"{voyage_type_emoji} {hosted.voyage_type.name.capitalize()
        if hosted.voyage_type else 'N/A'}",
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
        else f"{ANCIENT_COINS_EMOJI} 0",
        inline=True,
    )
    embed.add_field(
        name="Fish",
        value=f":fish: {hosted.fish_count:,}" if hosted.fish_count else ":fish: 0",
        inline=True,
    )

    log_channel = bot.get_channel(VOYAGE_LOGS)
    try:
        log_message: Message or None = await log_channel.fetch_message(int(hosted.log_id))
    except discord.errors.NotFound:
        log_message = None

    if log_message:
        embed.add_field(
            name="Created at", value=f"<t:{int(log_message.created_at.timestamp())}>", inline=True
        )
        if log_message.edited_at:
            embed.add_field(
                name="Edited at", value=f"<t:{int(log_message.edited_at.timestamp())}>", inline=True
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
            self.bot,
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
            self.bot,
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
            self.bot,
            self.hosted[self.selected_index],
            len(self.hosted),
            len(self.hosted) - self.selected_index,
        )
        await interaction.message.edit(embed=embed, view=self)
        # Acknowledge the interaction
        await interaction.response.defer()

    async def on_timeout(self):
        # Remove the view after 5 minutes
        self.stop()


class Logbook(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="logbook", description="Get information about a member")
    @app_commands.autocomplete(main_ship=autocomplete_main_ship)
    @app_commands.autocomplete(auxiliary_ship=autocomplete_auxiliary_ship)
    @app_commands.describe(
        ship_role="Filter by ship role",
        voyage_type="Filter by voyage type",
        host="Filter by host",
        crew_member="Filter by crew member",
    )
    @app_commands.choices(
        voyage_type=[
            app_commands.Choice(name="Patrol", value=VoyageType.PATROL.name),
            app_commands.Choice(name="Skirmish", value=VoyageType.SKIRMISH.name),
            app_commands.Choice(name="Adventure", value=VoyageType.ADVENTURE.name),
        ]
    )
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def logbook(
        self,
        interaction: discord.Interaction,
        main_ship: str = None,
        auxiliary_ship: str = None,
        ship_role: discord.Role = None,
        voyage_type: str = None,
        host: discord.Member = None,
        crew_member: discord.Member = None,
    ):
        if voyage_type and voyage_type not in VoyageType.__members__:
            return await interaction.response.send_message(
                embed=error_embed(title="Logbook Information", description="Invalid voyage type."),
                ephemeral=True,
            )

        if main_ship and not await is_valid_main_ship(main_ship):
            return await interaction.response.send_message(
                embed=error_embed(title="Logbook Information", description="Invalid main ship."),
                ephemeral=True,
            )

        if auxiliary_ship and not await is_valid_auxiliary_ship(auxiliary_ship):
            return await interaction.response.send_message(
                embed=error_embed(
                    title="Logbook Information", description="Invalid auxiliary ship."
                ),
                ephemeral=True,
            )

        if auxiliary_ship and main_ship:
            check_relation = await is_aux_part_of_main_ship(main_ship, auxiliary_ship)
            if not check_relation:
                return await interaction.response.send_message(
                    embed=error_embed(
                        title="Logbook Information",
                        description=f"{auxiliary_ship} is not part of {main_ship}.",
                    ),
                    ephemeral=True,
                )
            if isinstance(check_relation, list):
                return await interaction.response.send_message(
                    embed=error_embed(
                        title="Logbook Information",
                        description=f"{auxiliary_ship} is part of multiple "
                        f"ships: {', '.join(check_relation)}.",
                    ),
                    ephemeral=True,
                )

        hosted_repository = HostedRepository()
        hosted = hosted_repository.get_filtered_hosted(
            main_ship=main_ship,
            auxiliary_ship=auxiliary_ship,
            ship_role_id=ship_role.id if ship_role else None,
            voyage_type=voyage_type.upper() if voyage_type else None,
            host_id=host.id if host else None,
            crew_member_id=crew_member.id if crew_member else None,
        )

        if not hosted:
            return await interaction.response.send_message(
                embed=error_embed(title="Logbook Information", description="No logs found."),
                ephemeral=True,
            )

        embed = await build_embed(self.bot, hosted[0], len(hosted), len(hosted))
        view = LogBookView(self.bot, hosted)
        await interaction.response.send_message(embed=embed, view=view)

        hosted_repository.close_session()

    @logbook.error
    async def logbook_error(self, interaction: discord.Interaction, error: commands.CommandError):
        log.error("Error in logbook command")
        if isinstance(error, app_commands.errors.MissingAnyRole):
            await interaction.followup.send(
                embed=error_embed(
                    title="Missing Permissions", description="You lack the required permissions."
                ),
                ephemeral=True,
            )
        else:
            await interaction.followup.send(embed=error_embed(exception=error), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Logbook(bot))
