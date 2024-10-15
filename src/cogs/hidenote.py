import datetime
import discord
from discord.ext import commands
from discord import app_commands
from logging import getLogger

from src.config import SO_AND_UP
from src.data import Sailor, ModNotes
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.modnote_repository import ModNoteRepository
from src.utils.embeds import error_embed, default_embed

log = getLogger(__name__)


class HideNote(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="hidenote", description="Hide note on a Sailor Record (SO+)")
    @app_commands.describe(target="Select the user to hide the note for")
    @app_commands.describe(noteid="Enter the ID of the note to hide")
    @app_commands.checks.has_any_role(*SO_AND_UP)
    async def hidenote(self, interaction: discord.interactions, target: discord.Member = None, noteid: int = None):
        modnote_repository: ModNoteRepository = ModNoteRepository()
        sailor_repository: SailorRepository = SailorRepository()
        await interaction.response.defer (ephemeral=True)

        # Quick exit if no target or note is provided
        if target is None:
            await interaction.followup.send("You didn't add a target.")
            return
        if noteid is None:
            await interaction.followup.send("You didn't add a note id.")
            return

        # Attempt to update the information in the database
        try:
            # hide note
            mod_note : ModNotes = modnote_repository.hide_modnote(id=noteid,target_id=target.id,who_hid_id=interaction.user.id)

        except Exception as e:
            await interaction.followup.send(embed=error_embed("Failed to hide note. Please try again.", exception=e))
            return
        
        if mod_note:
            moderator = sailor_repository.get_sailor(interaction.user.id)
            if not moderator:
                await interaction.followup.send(embed=error_embed("Failed to get moderator information. Please try again."))
                return

            note_embed = default_embed(title=f"Note Hidden", description=f"Hid note {mod_note.id} for {target.mention}")
            note_embed.add_field(name="Moderator", value=f"<@{moderator.discord_id}>")
            note_embed.add_field(name="Note", value=mod_note.note)
            note_embed.add_field(name="Note Time", value=mod_note.note_time)
            note_embed.add_field(name="Hidden By", value=interaction.user.mention)
            await interaction.followup.send(embed=note_embed)
        else:
            await interaction.followup.send(embed=error_embed("Failled to hide note, please try again."))

        modnote_repository.close_session()
        sailor_repository.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(HideNote(bot))
