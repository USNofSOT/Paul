import os
import re
from logging import getLogger

import discord
from config import MINIMUM_GOLD_REQUIREMENT_FOR_PATROL, VOYAGE_PERMISSIONS
from config.emojis import ANCIENT_COINS_EMOJI, DOUBLOONS_EMOJI, GOLD_EMOJI
from data import VoyageType
from data.repository.voyage_repository import VoyageRepository
from discord import Colour, app_commands
from discord.ext import commands
from utils.ship_utils import convert_to_ordinal

from src.config import (
    CANNONEER_SYNONYMS,
    CARPENTER_SYNONYMS,
    FLEX_SYNONYMS,
    GRENADIER_SYNONYMS,
    GUILD_ID,
    HELM_SYNONYMS,
    NCO_AND_UP,
    NSC_ROLE,
    SURGEON_SYNONYMS,
    VOYAGE_LOGS,
)
from src.config.main_server import VOYAGE_PLANNING
from src.data import SubclassType
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import ensure_sailor_exists
from src.data.repository.subclass_repository import SubclassRepository
from src.utils.discord_utils import get_best_display_name
from src.utils.embeds import default_embed, error_embed

log = getLogger(__name__)


def retrieve_discord_id_from_process_line(line: str) -> int or None:
    """
    Retrieve the Discord ID from a line of text.

    Args:
        line (str): The line of text to extract the Discord ID from.
    Returns:
        int: The Discord ID extracted from the line of text.
    """
    pattern = r"<@!?(\d+)>"
    match = re.search(pattern, line)
    return int(match.group(1)) if match else None


subclass_map = {
    **{alias: SubclassType.CANNONEER for alias in CANNONEER_SYNONYMS},
    **{alias: SubclassType.FLEX for alias in FLEX_SYNONYMS},
    **{alias: SubclassType.CARPENTER for alias in CARPENTER_SYNONYMS},
    **{alias: SubclassType.HELM for alias in HELM_SYNONYMS},
}

subclass_repository = SubclassRepository()


def current_entries_embed(bot: commands.Bot, log_id: int, description: str = None) -> discord.Embed:
    """
    Generate an embed message containing all current subclass entries for
    a specific voyage log.

    Args:
        bot (commands.Bot): The bot instance.
        log_id (int): The ID of the voyage log.
        title (str): The title of the embed message.
        description (str): The description of the embed message
    Returns:
        discord.Embed: The embed message containing the subclass entries.
    """
    current_entries = subclass_repository.entries_for_log_id(log_id)

    if not current_entries:
        return error_embed(description="No subclass entries found for this voyage log")

    result_embed = discord.Embed(
        title=f"Subclasses for Voyage Log (https://discord.com/channels/{GUILD_ID}/{VOYAGE_LOGS}/{log_id})",
        description=description or "Displaying all subclasses currently logged for this voyage log",
        color=0x00FF00,
    )

    names, subclasses, counts = zip(
        *[
            (
                get_best_display_name(bot, entry.target_id),
                entry.subclass.value,
                str(entry.subclass_count),
            )
            for entry in current_entries
        ], strict=False
    )

    result_embed.add_field(name="Sailor", value="\n".join(names), inline=True)
    result_embed.add_field(name="Subclass", value="\n".join(subclasses), inline=True)
    result_embed.add_field(name="Count", value="\n".join(counts), inline=True)

    return result_embed


class ConfirmView(discord.ui.View):
    def __init__(
        self,
        interaction: discord.Interaction,
        bot: commands.Bot,
        updates: [any],
        missing_users: [int],
        author_id: int,
        log_id: str,
    ):
        self.interaction = interaction
        self.bot = bot
        self.author_id = author_id
        self.missing_users = missing_users
        self.log_id = log_id
        self.updates = updates
        super().__init__(timeout=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.interaction.delete_original_response()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get message for log id
        guild = self.bot.get_guild(GUILD_ID)
        logs_channel = guild.get_channel(VOYAGE_LOGS)
        log_message = await logs_channel.fetch_message(int(self.log_id))

        # Remove emoji send by bot discord py
        for reaction in log_message.reactions:
            if reaction.me:
                if str(os.getenv("ENVIRONMENT", "DEV")) == "PROD":
                    await reaction.clear()

        await interaction.response.send_message(
            "This may take a moment, please wait...", ephemeral=True
        )

        try:
            # Ensure the author exists in the database
            ensure_sailor_exists(self.author_id)

            for discord_id in self.missing_users:
                ensure_sailor_exists(discord_id)
                subclass_repository.delete_subclasses_for_target_in_log(discord_id, self.log_id)

            for discord_id, main_subclass, is_surgeon, grenadier_points in self.updates:
                # ensure the sailor exists in the database
                ensure_sailor_exists(discord_id)
                subclass_repository.delete_subclasses_for_target_in_log(discord_id, self.log_id)

                hosted_repository = HostedRepository()
                host = hosted_repository.get_host_by_log_id(self.log_id)
                if not host:
                    return await interaction.followup.send(
                        embed=error_embed(description="No hosted entry found for this voyage log"),
                        ephemeral=True,
                    )
                hosted_repository.close_session()

                try:
                    log.info("[%s] [Confirm] Adding subclasses for %s", self.log_id, discord_id)
                    subclass_repository.save_subclass(
                        self.author_id, self.log_id, discord_id, main_subclass
                    )
                    if is_surgeon:
                        log.info(
                            "[%s] [Confirm] Adding Surgeon subclass for %s", self.log_id, discord_id
                        )
                        subclass_repository.save_subclass(
                            self.author_id, self.log_id, discord_id, SubclassType.SURGEON
                        )
                    if grenadier_points > 0:
                        log.info(
                            "[%s] [Confirm] Adding %s Grenadier subclass for %s",
                            self.log_id,
                            grenadier_points,
                            discord_id,
                        )
                        subclass_repository.save_subclass(
                            self.author_id,
                            self.log_id,
                            discord_id,
                            SubclassType.GRENADIER,
                            grenadier_points,
                        )
                except Exception as e:
                    log.error("Error adding subclass: %s", e)
                    return await interaction.followup.send(
                        embed=error_embed(
                            description="An error occurred adding subclasses into the databasse",
                            exception=e,
                        ),
                        ephemeral=True,
                    )

            result_embed = current_entries_embed(self.bot, int(self.log_id))

            await interaction.delete_original_response()
            await self.interaction.edit_original_response(embed=result_embed, view=None)

            # Add reaction to the log message
            await log_message.add_reaction("<:Paul:1295457522102304820>")

        except Exception as e:
            log.error("Error occurred in confirm_button: %s", e)
            await interaction.followup.send(
                embed=error_embed(
                    description="An error occurred while processing the command", exception=e
                ),
                ephemeral=True,
            )
        finally:
            subclass_repository.close_session()


class AddSubclass(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="addsubclass",
        description="Add subclasses to Sailors based on a voyage log",
    )
    @app_commands.describe(
        log_id="The id of the voyage log to add subclasses from",
    )
    @app_commands.checks.has_any_role(*NCO_AND_UP, VOYAGE_PERMISSIONS)
    async def addsubclass(self, interaction: discord.Interaction, log_id: str):
        try:
            log.info(
                "--> [%s] addsubclass command received for log by %s", log_id, interaction.user.id
            )
            await interaction.response.defer(ephemeral=True)

            # Prepare the embed message
            embed = default_embed(
                title="Confirm Subclasses",
                description="Please confirm the subclasses to be added before continuing",
            )

            # Retrieve the logs channel
            try:
                logs_channel = self.bot.get_channel(VOYAGE_LOGS)
            except discord.NotFound as e:
                log.error("[%s] Unable to find the logs channel", log_id)
                return await interaction.followup.send(
                    embed=error_embed(description="Unable to find the logs channel", exception=e)
                )

            # Retrieve the log message
            try:
                log_message = await logs_channel.fetch_message(int(log_id))
            except discord.NotFound as e:
                log.warning("[%s] Unable to find the specified log", log_id)
                return await interaction.followup.send(
                    embed=error_embed(description="Unable to find the specified log", exception=e)
                )

            # Retrieve the author of the log
            log_author = log_message.author
            embed.set_author(name="Author: " + get_best_display_name(self.bot, log_author.id))
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            author_id = log_author.id

            log.info("[%s] Log author: %s", log_id, author_id)

            # Check if the interaction is from the author or an NSC member
            if author_id != interaction.user.id and NSC_ROLE not in [
                role.id for role in interaction.user.roles
            ]:
                return await interaction.followup.send(
                    embed=error_embed(description="You can only add subclasses to your own logs")
                )

            to_be_processed_lines = []
            # Go over each line in the log message
            # and prepare the lines to be processed for adding subclasses
            for line in log_message.content.split("\n"):
                if not line:
                    continue

                if "<@" in line and "log" not in line.lower():
                    to_be_processed_lines.append(line)
                    log.debug("[%s] Found line to be processed: %s", log_id, line)

            current_entries = subclass_repository.entries_for_log_id(int(log_id))
            users_found_in_database = [entry.target_id for entry in current_entries]
            users_found_in_processed_lines = []

            log.info("[%s] Found %s lines to be processed", log_id, len(to_be_processed_lines))
            log.info("[%s] Found %s entries in the database", log_id, len(users_found_in_database))
            log.info(
                "[%s] Found %s users in the processed lines",
                log_id,
                len(users_found_in_processed_lines),
            )

            # A duplicate is an update that is fully present in the database,
            # this means every entry of it
            duplicates = []
            # A list of updates to be made
            updates = []

            for process_line in to_be_processed_lines:
                log.info("[%s] Processing line: %s", log_id, process_line)
                # Retrieve the Discord ID from the line
                discord_id = retrieve_discord_id_from_process_line(process_line)
                if not discord_id:
                    continue

                # Get users name from GUILD or Anonymous
                user_name = get_best_display_name(self.bot, discord_id)

                # Check for main subclasses
                main_subclass = None
                for alias, subclass in subclass_map.items():
                    if alias in process_line.lower():
                        log.info("[%s] Found main subclass %s for %s", log_id, subclass, discord_id)
                        main_subclass = subclass
                        break

                if not main_subclass:
                    log.warning(
                        "[%s] No main subclass found for mention, "
                        "will not be considered for this log",
                        log_id,
                    )
                    embed.add_field(
                        name=f"{user_name} - :warning:",
                        value="No main subclass found for mention, "
                        "will not be considered for this log",
                        inline=False,
                    )
                    continue
                else:
                    users_found_in_processed_lines.append(discord_id)

                if not main_subclass:
                    log.error(
                        "[%s] No main subclass found for mention, "
                        "will not be considered for this log",
                        log_id,
                    )
                    await interaction.followup.send(
                        embed=error_embed(
                            description="Couldn't process the log properly, "
                            "please ensure the log is formatted correctly"
                        )
                    )
                    return

                # Check if the user is Surgeon
                surgeon = False
                if any(alias in process_line.lower() for alias in SURGEON_SYNONYMS):
                    log.info("Adding Surgeon subclass to %s", discord_id)
                    surgeon = True

                # Check how many times any Grenadier synonym is found in the line
                grenadier = 0
                for alias in GRENADIER_SYNONYMS:
                    grenadier += process_line.lower().count(alias.lower())
                log.info(
                    "[%s] Found %s amount of Grenadier subclasses for %s",
                    log_id,
                    grenadier,
                    discord_id,
                )

                # Get all entries for the current user and log
                relative_entries = [
                    entry
                    for entry in current_entries
                    if entry.target_id == discord_id and entry.log_id == int(log_id)
                ]
                log.info(
                    "[%s] Found %s relative entries for %s",
                    log_id,
                    len(relative_entries),
                    discord_id,
                )

                is_new = True
                requires_update = False
                log.info("[%s] Checking if subclasses are new or require an update", log_id)
                log.info(
                    "[%s] Main subclass: %s, Surgeon: %s, Grenadier: %s",
                    log_id,
                    main_subclass,
                    surgeon,
                    grenadier,
                )
                log.info("[%s] is_new: %s, requires_update: %s", log_id, is_new, requires_update)

                if any(entry.subclass == main_subclass for entry in relative_entries):
                    is_new = False

                if surgeon and any(
                    entry.subclass == SubclassType.SURGEON for entry in relative_entries
                ):
                    is_new = False

                if grenadier > 0 and any(
                    entry.subclass == SubclassType.GRENADIER for entry in relative_entries
                ):
                    is_new = False

                requires_update = (
                    not any(entry.subclass == main_subclass for entry in relative_entries)
                    or (
                        surgeon
                        and not any(
                            entry.subclass == SubclassType.SURGEON for entry in relative_entries
                        )
                    )
                    or (
                        0
                        < grenadier
                        != sum(
                            entry.subclass_count
                            for entry in relative_entries
                            if entry.subclass == SubclassType.GRENADIER
                        )
                    )
                    or (
                        grenadier == 0
                        and any(
                            entry.subclass == SubclassType.GRENADIER for entry in relative_entries
                        )
                    )
                )

                if not surgeon and any(
                    entry.subclass == SubclassType.SURGEON for entry in relative_entries
                ):
                    requires_update = True

                if not requires_update:
                    log.warning("Skipping %s as all subclasses already exist", discord_id)
                    duplicates.append(process_line)
                    continue

                emoji = ":new:" if is_new else ":repeat:"

                updates.append((discord_id, main_subclass, surgeon, grenadier))

                embed_value = f"Main Subclass: {main_subclass.value}"
                if surgeon:
                    embed_value += f"\nSurgeon Pts.: {1}"
                if grenadier > 0:
                    embed_value += f"\nGrenadier Pts.: {grenadier}"

                embed.add_field(name=f"{user_name} - {emoji}", value=embed_value, inline=False)

            missing_users = {
                entry.target_id
                for entry in current_entries
                if entry.target_id not in users_found_in_processed_lines
            }
            log.info("[%s] Missing users: %s", log_id, missing_users)

            for missing_users_id in missing_users:
                user_name = get_best_display_name(self.bot, missing_users_id)
                embed.add_field(
                    name=f"{user_name} - :x:",
                    value="Sailor no longer in the log, removing on confirmation",
                    inline=False,
                )

            log.info("[%s] duplicates: %s", log_id, duplicates)
            if duplicates:
                embed.set_footer(
                    text=f"{len(duplicates)} out of {len(to_be_processed_lines)} entries "
                    f"were duplicates and were removed from this list."
                )
            if len(duplicates) == len(to_be_processed_lines) and len(missing_users) == 0:
                return await interaction.followup.send(
                    embed=current_entries_embed(
                        self.bot,
                        int(log_id),
                        description=f"All entries ({len(duplicates)}) were duplicates. "
                        f"Displaying current entries.",
                    )
                )
            log.info("[%s] pending updates: %s", log_id, updates)
            if len(updates) == 0 and len(missing_users) == 0:
                return await interaction.followup.send(
                    embed=current_entries_embed(
                        self.bot,
                        int(log_id),
                        description="No updates had to be made. Displaying current entries.",
                    )
                )
            embed_misc_voyage_info = discord.Embed(
                title="Miscellaneous Voyage Information",
                description="The following information was found in the voyage log"
                ", please ensure all information "
                "including spelling and capitalization is correct. "
                "Gold and Doubloon counts should be fully written out.",
                color=Colour.green(),
            )

            embed_misc_voyage_info.add_field(
                name="Log Link",
                value=f"https://discord.com/channels/{GUILD_ID}/{VOYAGE_LOGS}/{log_id}",
                inline=False,
            )
            hosted_repository = HostedRepository()
            hosted_entry = hosted_repository.get_host_by_log_id(int(log_id))
            previous_count = hosted_repository.get_previous_ship_voyage_count(log_id)
            hosted_repository.close_session()

            warnings = []
            print(hosted_entry)
            if hosted_entry.voyage_planning_message_id:
                embed_misc_voyage_info.add_field(
                    name="Voyage Planning",
                    value=f"https://discord.com/channels/{GUILD_ID}/{VOYAGE_PLANNING}/"
                          f"{hosted_entry.voyage_planning_message_id}",
                    inline=False,
                )
            else:
                embed_misc_voyage_info.add_field(
                    name="Voyage Planning",
                    value=":information_source: `Unknown`",
                    inline=False,
                )

            if hosted_entry.ship_name:
                embed_misc_voyage_info.add_field(
                    name="Main Ship",
                    value=":white_check_mark: " + hosted_entry.ship_name,
                )
            else:
                embed_misc_voyage_info.add_field(
                    name="Main Ship",
                    value=":warning: Unknown",
                )
                warnings.append("No main ship found")

            embed_misc_voyage_info.add_field(
                name="Auxiliary Ship",
                value=":white_check_mark: " + hosted_entry.auxiliary_ship_name
                if hosted_entry.auxiliary_ship_name
                else ":information_source: None",
            )

            embed_misc_voyage_info.add_field(
                name="Host", value=f"<@{hosted_entry.target_id}>", inline=True
            )

            if hosted_entry.ship_voyage_count < 0:
                embed_misc_voyage_info.add_field(
                    name="Voyage Count",
                    value=":warning: `Unknown`",
                )
                warnings.append("Unknown voyage count")
            else:
                if previous_count:
                    if previous_count + 1 == hosted_entry.ship_voyage_count:
                        embed_misc_voyage_info.add_field(
                            name="Voyage Count",
                            value=f":white_check_mark: "
                            f"{convert_to_ordinal(hosted_entry.ship_voyage_count)}",
                        )
                    else:
                        embed_misc_voyage_info.add_field(
                            name="Voyage Count",
                            value=f":warning: "
                            f"`{convert_to_ordinal(hosted_entry.ship_voyage_count)} "
                            f"(Expected {convert_to_ordinal(previous_count + 1)})`",
                        )
                        warnings.append(
                            f"Expected voyage count: {convert_to_ordinal(previous_count + 1)}"
                        )
                else:
                    embed_misc_voyage_info.add_field(
                        name="Voyage Count",
                        value=f":new: {convert_to_ordinal(hosted_entry.ship_voyage_count)}",
                    )

            if hosted_entry.voyage_type.value != VoyageType.UNKNOWN.value:
                embed_misc_voyage_info.add_field(
                    name="Voyage Type",
                    value=f":white_check_mark: {hosted_entry.voyage_type.value}",
                )
            else:
                embed_misc_voyage_info.add_field(
                    name="Voyage Type",
                    value=":warning: `Unknown`",
                )
                warnings.append("Unknown voyage type")

            crew_string = ""
            voyage_repository = VoyageRepository()
            for voyage in voyage_repository.get_voyages_by_log_id(int(log_id)):
                crew_string += f"<@{voyage.target_id}> \n"
            embed_misc_voyage_info.add_field(name="Crew", value=crew_string)
            voyage_repository.close_session()

            generic_loot_confiscated_string = (
                f"{GOLD_EMOJI} Gold: {hosted_entry.gold_count:,}\n"
                f"{DOUBLOONS_EMOJI} Doubloons: {hosted_entry.doubloon_count:,}\n"
            )

            misc_loot_confiscated_string = (
                f"{ANCIENT_COINS_EMOJI} Ancient Coins: {hosted_entry.ancient_coin_count:,}\n"
                f":fish: Fish: {hosted_entry.fish_count:,}"
            )

            embed_misc_voyage_info.add_field(
                name="Generic confiscated:", value=generic_loot_confiscated_string
            )

            embed_misc_voyage_info.add_field(
                name="Miscellaneous confiscated:",
                value=misc_loot_confiscated_string,
            )

            if hosted_entry.voyage_type.name == VoyageType.PATROL.name:
                if hosted_entry.gold_count <= 0:
                    warnings.append("Patrol with no gold count")
                elif hosted_entry.gold_count < MINIMUM_GOLD_REQUIREMENT_FOR_PATROL:
                    warnings.append(
                        "Patrol has gold count lower than the minimum requirement: %s"
                        % MINIMUM_GOLD_REQUIREMENT_FOR_PATROL
                    )

            if (
                hosted_entry.auxiliary_ship_name
                and hosted_entry.ship_name == hosted_entry.auxiliary_ship_name
            ):
                warnings.append("Main ship and auxiliary ship are the same")

            if warnings:
                embed_misc_voyage_info.colour = Colour.yellow()
                embed_misc_voyage_info.set_footer(
                    text="If you think this is an error please contact the NSC Department."
                )
                embed_misc_voyage_info.add_field(name="\u200b", value="\u200b", inline=False)
                embed_misc_voyage_info.add_field(
                    name=r":warning: Warnings",
                    value="\n".join([f"- {warning}" for warning in warnings]),
                    inline=False,
                )

            await interaction.followup.send(
                embeds=[embed_misc_voyage_info, embed],
                view=ConfirmView(interaction, self.bot, updates, missing_users, author_id, log_id),
            )
        except Exception as e:
            log.exception("Error occurred in addsubclass command: %s", e)
            await interaction.followup.send(
                embed=error_embed(
                    description="An error occurred while processing the command", exception=e
                ),
                ephemeral=True,
            )

    @addsubclass.error
    async def addsubclass_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        log.error("Error occurred in addsubclass command: %s", error)
        if isinstance(error, app_commands.errors.MissingAnyRole):
            embed = error_embed(
                title="Missing Permissions",
                description="You do not have the required permissions to use this command.",
                footer=False,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AddSubclass(bot))
