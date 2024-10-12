import re
from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import sessionmaker

from src.config import VOYAGE_LOGS, NSC_ROLE, CANNONEER_SYNONYMS, FLEX_SYNONYMS, CARPENTER_SYNONYMS, HELM_SYNONYMS, \
    SURGEON_SYNONYMS, GRENADIER_SYNONYMS, NCO_AND_UP
from src.data import SubclassType, engine
from src.data.repository.sailor_repository import ensure_sailor_exists
from src.data.repository.subclass_repository import save_subclass
from src.utils.embeds import error_embed, default_embed

log = getLogger(__name__)


def retrieve_discord_id_from_process_line(line: str) -> int:
    """
    Retrieve the Discord ID from a line of text.

    Args:
        line (str): The line of text to extract the Discord ID from.
    Returns:
        int: The Discord ID extracted from the line of text.
    """
    pattern = r"<@!?(\d+)>"
    match = re.search(pattern, line)
    return int(match.group(1))


subclass_map = {
    **{alias: SubclassType.CANNONEER for alias in CANNONEER_SYNONYMS},
    **{alias: SubclassType.FLEX for alias in FLEX_SYNONYMS},
    **{alias: SubclassType.CARPENTER for alias in CARPENTER_SYNONYMS},
    **{alias: SubclassType.HELM for alias in HELM_SYNONYMS},
}


class ConfirmView(discord.ui.View):
    def __init__(self, updates, author_id, log_id):
        self.author_id = author_id
        self.log_id = log_id
        self.updates = updates
        super().__init__(timeout=None)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"Attempting to add subclasses...", ephemeral=True)

        # Ensure the author exists in the database
        ensure_sailor_exists(self.author_id)

        for discord_id, main_subclass, is_surgeon, grenadier_points in self.updates:
            # ensure the sailor exists in the database
            ensure_sailor_exists(discord_id)
            try:
                log.debug(f"Adding main subclass {main_subclass} to {discord_id}")
                save_subclass(self.author_id, self.log_id, discord_id, main_subclass)
                if is_surgeon:
                    log.debug(f"Adding Surgeon subclass to {discord_id}")
                    save_subclass(self.author_id, self.log_id, discord_id, SubclassType.SURGEON)
                if grenadier_points > 0:
                    log.debug(f"Adding {grenadier_points} Grenadier subclass to {discord_id}")
                    save_subclass(self.author_id, self.log_id, discord_id, SubclassType.GRENADIER, grenadier_points)
            except Exception as e:
                log.error(f"Error adding subclass: {e}")
                return await interaction.followup.send(embed=error_embed(description="An error occurred while adding subclasses"))
        # End the interaction
        # Edit the original message to inform the user that the subclasses were added successfully
        await interaction.followup.send(":white_check_mark: Subclasses added successfully", ephemeral=True)


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
    @app_commands.checks.has_any_role(*NCO_AND_UP)
    async def addsubclass(self, interaction: discord.Interaction, log_id: str):
        log.info(f"Received addsubclass command with log_id: {log_id}")
        await interaction.response.defer(ephemeral=True)

        # Prepare the embed message
        embed = default_embed(title="Confirm Subclasses",
                              description="Please confirm the subclasses to be added before confirming.")

        # Retrieve the logs channel
        try:
            logs_channel = self.bot.get_channel(VOYAGE_LOGS)
        except discord.NotFound:
            return await interaction.followup.send(embed=error_embed(description="The logs channel is not found"))

        # Retrieve the log message
        try:
            log_message = await logs_channel.fetch_message(int(log_id))
        except discord.NotFound:
            return await interaction.followup.send(embed=error_embed(description="The log message is not found"))

        # Retrieve the author of the log
        log_author = log_message.author
        embed.set_author(name="Author: " + self.bot.get_guild(log_message.guild.id).get_member(log_author.id).display_name)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        author_id = log_author.id

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

        updates = []
        for process_line in to_be_processed_lines:
            log.debug(f"Processing line: {process_line}")
            # Retrieve the Discord ID from the line
            discord_id = retrieve_discord_id_from_process_line(process_line)
            # Get users name from GUILD or Anonymous
            user_name = "Anonymous"
            user = self.bot.get_user(discord_id)
            if user:
                user_name = self.bot.get_guild(log_message.guild.id).get_member(discord_id).display_name

            # Check for main subclasses
            main_subclass = None
            for alias, subclass in subclass_map.items():
                if alias in process_line.lower():
                    log.debug(f"Adding {subclass} subclass to {discord_id}")
                    main_subclass = subclass
                    break
            if not main_subclass:
                log.error(f"No subclasses matches found in the line: {process_line}")
                await interaction.followup.send(
                    embed=error_embed(description="Not all subclasses were found in the log message"))
                return

            # Check if the user is Surgeon
            surgeon = False
            if any(alias in process_line.lower() for alias in SURGEON_SYNONYMS):
                log.debug(f"Adding Surgeon subclass to {discord_id}")
                surgeon = True

            # Check how many times any Grenadier synonym is found in the line
            # This can be Synonym1, Synonym1 but also Synonym1, Synonym2
            grenadier = 0
            for alias in GRENADIER_SYNONYMS:
                grenadier += process_line.lower().count(alias.lower())

            embed.add_field(
                # mention the user
                name=f"{user_name}",
                value=f"Main Subclass: {main_subclass.value}\n"
                      f"Surgeon Pts.: {1 if surgeon else 0}\n"
                      f"Grenadier Pts.: {grenadier}",
                inline=False,
            )

            updates.append((discord_id, main_subclass, surgeon, grenadier))

        view = ConfirmView(updates, author_id, log_id)

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(AddSubclass(bot))
