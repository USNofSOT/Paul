import re
from logging import getLogger

import discord
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


subclass_map = {**{alias: SubclassType.CANNONEER for alias in CANNONEER_SYNONYMS},
    **{alias: SubclassType.FLEX for alias in FLEX_SYNONYMS},
    **{alias: SubclassType.CARPENTER for alias in CARPENTER_SYNONYMS},
    **{alias: SubclassType.HELM for alias in HELM_SYNONYMS}, }

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
        description=description or "Displaying all subclasses currently logged for this voyage log", color=0x00FF00)

    names, subclasses, counts = zip(
        *[(get_best_display_name(bot, entry.target_id), entry.subclass.value, str(entry.subclass_count)) for entry in
            current_entries])

    result_embed.add_field(name="Sailor", value="\n".join(names), inline=True)
    result_embed.add_field(name="Subclass", value="\n".join(subclasses), inline=True)
    result_embed.add_field(name="Count", value="\n".join(counts), inline=True)

    return result_embed


class ConfirmView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, bot: commands.Bot, updates: [any], missing_users: [int],
                 author_id: int, log_id: str):
        self.interaction = interaction
        self.bot = bot
        self.author_id = author_id
        self.missing_users = missing_users
        self.log_id = log_id
        self.updates = updates
        super().__init__(timeout=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message = await self.interaction.delete_original_response()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get message for log id
        guild = self.bot.get_guild(GUILD_ID)
        logs_channel = guild.get_channel(VOYAGE_LOGS)
        log_message = await logs_channel.fetch_message(int(self.log_id))

        # Remove emoji send by bot discord py
        for reaction in log_message.reactions:
            if reaction.me:
                await reaction.clear()

        wait = await interaction.response.send_message("This may take a moment, please wait...", ephemeral=True)

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
                        embed=error_embed(description="No hosted entry found for this voyage log"), ephemeral=True)
                hosted_repository.close_session()

                try:
                    log.info(f"[{self.log_id}] [Confirm] Adding subclasses for {discord_id}")
                    subclass_repository.save_subclass(self.author_id, self.log_id, discord_id, main_subclass)
                    if is_surgeon:
                        log.info(f"[{self.log_id}] [Confirm] Adding Surgeon subclass for {discord_id}")
                        subclass_repository.save_subclass(self.author_id, self.log_id, discord_id, SubclassType.SURGEON)
                    if grenadier_points > 0:
                        log.info(f"[{self.log_id}] [Confirm] Adding {grenadier_points} Grenadier subclass for {discord_id}")
                        subclass_repository.save_subclass(self.author_id, self.log_id, discord_id,
                                                          SubclassType.GRENADIER, grenadier_points)
                except Exception as e:
                    log.error(f"Error adding subclass: {e}")
                    return await interaction.followup.send(
                        embed=error_embed(description="An error occurred adding subclasses into the databasse",
                                          exception=e), ephemeral=True)

            result_embed = current_entries_embed(self.bot, int(self.log_id))

            await interaction.delete_original_response()
            await self.interaction.edit_original_response(embed=result_embed, view=None)

            # Add reaction to the log message
            await log_message.add_reaction("<:Paul:1295457522102304820>")

        except Exception as e:
            log.error(f"Error occurred in confirm_button: {e}")
            await interaction.followup.send(
                embed=error_embed(description="An error occurred while processing the command", exception=e),
                ephemeral=True)
        finally:
            subclass_repository.close_session()


class AddSubclass(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="addsubclass", description="Add subclasses to Sailors based on a voyage log", )
    @app_commands.describe(log_id="The id of the voyage log to add subclasses from", )
    @app_commands.checks.has_any_role(*NCO_AND_UP)
    async def addsubclass(self, interaction: discord.Interaction, log_id: str):
        try:
            log.info(f"--> [{log_id}] addsubclass command received for log by {interaction.user.id}")
            await interaction.response.defer(ephemeral=True)

            # Prepare the embed message
            embed = default_embed(title="Confirm Subclasses",
                                  description="Please confirm the subclasses to be added before continuing")

            # Retrieve the logs channel
            try:
                logs_channel = self.bot.get_channel(VOYAGE_LOGS)
            except discord.NotFound as e:
                log.error(f"[{log_id}] Unable to find the logs channel")
                return await interaction.followup.send(
                    embed=error_embed(description="Unable to find the logs channel", exception=e))

            # Retrieve the log message
            try:
                log_message = await logs_channel.fetch_message(int(log_id))
            except discord.NotFound as e:
                log.warning(f"[{log_id}] Unable to find the specified log")
                return await interaction.followup.send(
                    embed=error_embed(description="Unable to find the specified log", exception=e))

            # Retrieve the author of the log
            log_author = log_message.author
            embed.set_author(name="Author: " + get_best_display_name(self.bot, log_author.id))
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            author_id = log_author.id

            log.info(f"[{log_id}] Log author: {author_id}")

            # Check if the interaction is from the author or an NSC member
            if author_id != interaction.user.id and NSC_ROLE not in [role.id for role in interaction.user.roles]:
                return await interaction.followup.send(
                    embed=error_embed(description="You can only add subclasses to your own logs"))

            to_be_processed_lines = []
            # Go over each line in the log message and prepare the lines to be processed for adding subclasses
            for line in log_message.content.split("\n"):
                if not line:
                    continue

                if "<@" in line and 'log' not in line.lower():
                    to_be_processed_lines.append(line)
                    log.debug(f"Found line to be processed: {line}")

            current_entries = subclass_repository.entries_for_log_id(int(log_id))
            users_found_in_database = [entry.target_id for entry in current_entries]
            users_found_in_processed_lines = []

            log.info(f"[{log_id}] Found {len(to_be_processed_lines)} lines to be processed")
            log.info(f"[{log_id}] Found {len(users_found_in_database)} entries in the database")
            log.info(f"[{log_id}] Found {len(users_found_in_processed_lines)} users in the processed lines")

            # A duplicate is an update that is fully present in the database, this means every entry of it
            duplicates = []
            # A list of updates to be made
            updates = []

            for process_line in to_be_processed_lines:
                log.info(f"[{log_id}] Processing line: {process_line}")
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
                        log.info(f"[{log_id}] Found main subclass {subclass} for {discord_id}")
                        main_subclass = subclass
                        break

                if not main_subclass:
                    log.warning(f"[{log_id}] No main subclass found for mention, will not be considered for this log")
                    embed.add_field(name=f"{user_name} - :warning:",
                        value="No main subclass found for mention, will not be considered for this log", inline=False, )
                    continue
                else:
                    users_found_in_processed_lines.append(discord_id)

                if not main_subclass:
                    log.error(f"[{log_id}] No main subclass found for mention, will not be considered for this log")
                    await interaction.followup.send(embed=error_embed(
                        description="Couldn't process the log properly, please ensure the log is formatted correctly"))
                    return

                # Check if the user is Surgeon
                surgeon = False
                if any(alias in process_line.lower() for alias in SURGEON_SYNONYMS):
                    log.info(f"Adding Surgeon subclass to {discord_id}")
                    surgeon = True

                # Check how many times any Grenadier synonym is found in the line
                # This can be Synonym1, Synonym1 but also Synonym1, Synonym2
                grenadier = 0
                for alias in GRENADIER_SYNONYMS:
                    grenadier += process_line.lower().count(alias.lower())
                log.info(f"[{log_id}] Found {grenadier} amount of Grenadier subclasses for {discord_id}")

                # Get all entries for the current user and log
                relative_entries = [entry for entry in current_entries if
                                    entry.target_id == discord_id and entry.log_id == int(log_id)]
                log.info(f"[{log_id}] Found {len(relative_entries)} relative entries for {discord_id}")

                # Keep track of whether the subclass is new or requires an update
                is_new = True
                requires_update = False
                log.info(f"[{log_id}] Checking if subclasses are new or require an update")
                log.info(f"[{log_id}] Main subclass: {main_subclass}, Surgeon: {surgeon}, Grenadier: {grenadier}")
                log.info(f"[{log_id}] is_new: {is_new}, requires_update: {requires_update}")

                # Check if any of the subclasses are already in the database
                if any(entry.subclass == main_subclass for entry in relative_entries):
                    is_new = False  # Main subclass already exists

                # Check if Surgeon subclass is already in the database
                if surgeon and any(entry.subclass == SubclassType.SURGEON for entry in relative_entries):
                    is_new = False  # Surgeon subclass already exists

                # Check if Grenadier subclass is already in the database
                if grenadier > 0 and any(entry.subclass == SubclassType.GRENADIER for entry in relative_entries):
                    is_new = False  # Grenadier subclass already exists

                # Now check if update is needed (i.e., if any subclass is missing)
                requires_update = (not any(entry.subclass == main_subclass for entry in relative_entries) or (
                            surgeon and not any(
                        entry.subclass == SubclassType.SURGEON for entry in relative_entries)) or (0 < grenadier != sum(
                    entry.subclass_count for entry in relative_entries if entry.subclass == SubclassType.GRENADIER)) or
                   (grenadier == 0 and any(
                       entry.subclass == SubclassType.GRENADIER for entry in relative_entries))
                   )


                if not surgeon and any(entry.subclass == SubclassType.SURGEON for entry in relative_entries):
                    requires_update = True

                # If no update is required, add to duplicates and skip
                if not requires_update:
                    log.warning(f"Skipping {discord_id} as all subclasses already exist")
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

            missing_users = {entry.target_id for entry in current_entries if
                             entry.target_id not in users_found_in_processed_lines}
            log.info(f"[{log_id}] Missing users: {missing_users}")

            for missing_users_id in missing_users:
                user_name = get_best_display_name(self.bot, missing_users_id)
                embed.add_field(name=f"{user_name} - :x:",
                    value="Sailor no longer in the log, removing on confirmation", inline=False, )

            log.info(f"[{log_id}] duplicates: {duplicates}")
            if duplicates:
                embed.set_footer(
                    text=f"{len(duplicates)} out of {len(to_be_processed_lines)} entries were duplicates and were removed from this list.")
            if len(duplicates) == len(to_be_processed_lines) and len(missing_users) == 0:
                return await interaction.followup.send(embed=current_entries_embed(self.bot, int(log_id),
                                                                                   description=f"All entries ({len(duplicates)}) were duplicates. Displaying current entries."))
            log.info(f"[{log_id}] pending updates: {updates}")
            if len(updates) == 0 and len(missing_users) == 0:
                return await interaction.followup.send(embed=current_entries_embed(self.bot, int(log_id),
                                                                                   description="No updates had to be made. Displaying current entries."))
            embed_misc_voyage_info = discord.Embed(
                title="Miscellaneous Voyage Information",
                description="The following information was found in the voyage log, please ensure all information including spelling and capitalization is correct. Gold and Doubloon counts should be fully written out.",
                color=Colour.dark_gold(),
            )

            embed_misc_voyage_info.add_field(name="Log Link", value=f"https://discord.com/channels/{GUILD_ID}/{VOYAGE_LOGS}/{log_id}", inline=False)
            hosted_repository = HostedRepository()
            hosted_entry = hosted_repository.get_host_by_log_id(int(log_id))
            previous_count = hosted_repository.get_previous_ship_voyage_count(log_id)
            hosted_repository.close_session()

            embed_misc_voyage_info.add_field(
                name="Main Ship",
                value=hosted_entry.ship_name or ":warning: Unknown",
            )
            embed_misc_voyage_info.add_field(
                name="Auxiliary Ship",
                value=hosted_entry.auxiliary_ship_name or ":information_source: None",
            )

            if hosted_entry.ship_voyage_count < 0:
                embed_misc_voyage_info.add_field(
                    name="Voyage Count",
                    value=":warning: Unknown",
                )
            else:
                if previous_count:
                    if previous_count + 1 == hosted_entry.ship_voyage_count:
                        embed_misc_voyage_info.add_field(
                            name="Voyage Count",
                            value=f":white_check_mark: {convert_to_ordinal(hosted_entry.ship_voyage_count)}",
                        )
                    else:
                        embed_misc_voyage_info.add_field(
                            name="Voyage Count",
                            value=f":warning: {convert_to_ordinal(hosted_entry.ship_voyage_count)} (Expected {convert_to_ordinal(previous_count + 1)})",
                        )
                else:
                    embed_misc_voyage_info.add_field(
                        name="Voyage Count",
                        value=f":new: {convert_to_ordinal(hosted_entry.ship_voyage_count)}",
                )

            gold_emoji = "<:Gold:965929014067867699>"

            embed_misc_voyage_info.add_field(
                name=f"{gold_emoji} Count",
                value=f"{hosted_entry.gold_count:,}" if hosted_entry.gold_count is not None else ":information_source: Unknown",
            )

            doubloon_emoji = "<:Doubloon:965929088650981426>"

            embed_misc_voyage_info.add_field(
                name=f"{doubloon_emoji} Count",
                value=f"{hosted_entry.doubloon_count:,}" if hosted_entry.doubloon_count is not None else ":information_source: Unknown",
            )

            await interaction.followup.send(embeds=[embed_misc_voyage_info, embed],
                                            view=ConfirmView(interaction, self.bot, updates, missing_users, author_id,
                                                             log_id))
        except Exception as e:
            log.error(f"Error occurred in addsubclass command: {e}", exc_info=True)
            await interaction.followup.send(
                embed=error_embed(description="An error occurred while processing the command", exception=e),
                ephemeral=True)

    @addsubclass.error
    async def addsubclass_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        log.error(f"Error occurred in addsubclass command: {error}")
        if isinstance(error, app_commands.errors.MissingAnyRole):
            embed = error_embed(title="Missing Permissions",
                                description="You do not have the required permissions to use this command.",
                                footer=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AddSubclass(bot))