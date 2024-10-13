import datetime
import discord
from discord.ext import commands
from discord import app_commands
from logging import getLogger

from src.config import SNCO_AND_UP
from src.data import Sailor, ModNotes
from src.data.repository.sailor_repository import SailorRepository
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
        modnote_repo = ModNoteRepository()

        # Quick exit if no target or note is provided
        if target is None:
            await interaction.followup.send("You didn't add a target.")
            return
        if note is None:
            await interaction.followup.send("You didn't add a note.")
            return

        # Attempt to add the information to the database
        try:
            # Create ModNote
            modnote_repo.create_modnote(target_id=target.id,
                                        moderator_id=interaction.user.id,
                                        note=note,
                                        note_time=datetime.datetime.now())
            modnote_repo.close_session()
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Failed to add note. Please try again.", exception=e))
            return


async def setup(bot: commands.Bot):
    await bot.add_cog(AddNote(bot))
