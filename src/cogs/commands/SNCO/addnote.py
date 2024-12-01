import datetime
import discord
from discord.ext import commands
from discord import app_commands
from logging import getLogger

from src.config import SNCO_AND_UP
from src.data import ModNotes
from src.data.repository.modnote_repository import ModNoteRepository
from src.utils.embeds import error_embed, default_embed

log = getLogger(__name__)


class AddNote(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="addnote", description="Add a note to a Sailor Record (SNCO+)")
    @app_commands.describe(target="Select the user to add the note to")
    @app_commands.describe(note="Write the note to add to the sailor")
    @app_commands.checks.has_any_role(*SNCO_AND_UP)
    async def addnote(self, interaction: discord.interactions, target: discord.Member = None, note: str = None):
        await interaction.response.defer (ephemeral=True)

        # Quick exit if no target or note is provided
        if target is None:
            await interaction.followup.send("You didn't add a target.")
            return
        if note is None:
            await interaction.followup.send("You didn't add a note.")
            return

        # Attempt to add the information to the database
        try:
            mod_note : ModNotes = ModNoteRepository().create_modnote(target_id=target.id,
                                                                     moderator_id=interaction.user.id,
                                                                     note=note)

        except Exception as e:
            await interaction.followup.send(embed=error_embed("Failed to add note. Please try again.", exception=e))
            return
        
        # Print note or error, as confirmation
        if mod_note:
            note_embed = default_embed(title="Note Added", description=f"Displaying note for {target.mention}")
            note_embed.add_field(name="Moderator", value=interaction.user.mention)
            note_embed.add_field(name="Note", value=note)
            await interaction.followup.send(embed=note_embed)
        else:
            await interaction.followup.send(embed=error_embed("Failled to add note, please try again."))


async def setup(bot: commands.Bot):
    await bot.add_cog(AddNote(bot))
