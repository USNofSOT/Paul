import discord
from discord import app_commands
from discord.ext import commands

from src.config.ranks_roles import SNCO_AND_UP, NSC_ROLE, BOA_ROLE
from src.data import ModNotes
from src.data.repository.modnote_repository import ModNoteRepository
from src.utils.embeds import default_embed
from src.utils.time_utils import format_time, get_time_difference_past


class ShowNotes(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="shownotes", description="Show the 25 most recent notes for a user")
    @app_commands.checks.has_any_role(*SNCO_AND_UP)
    async def view_moderation(self, interaction: discord.interactions, target: discord.Member = None):
        if target is None:
            target = interaction.user

        embed = default_embed(
            title=f"Showing Notes",
            description=f"{target.mention}",
            author=False
        )
        try:
            avatar_url = target.guild_avatar.url if target.guild_avatar else target.avatar.url
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass


        mod_note_repository = ModNoteRepository()
        interaction_user_roles = [role.id for role in interaction.user.roles]
        is_boa = BOA_ROLE in interaction_user_roles

        mod_notes: [ModNotes] = mod_note_repository.get_modnotes(target_id=target.id, limit=25, show_hidden=is_boa)
        mod_notes_total: int = mod_note_repository.count_modnotes(target.id, include_hidden=is_boa)
        mod_note_string = "\n".join(
            f"<@{mod_note.moderator_id}>: {mod_note.note} _({format_time(get_time_difference_past(mod_note.note_time))} ago)_{' (`HIDDEN`)' if mod_note.hidden else ''}"
            for mod_note in mod_notes
        )
        mod_note_repository.close_session()
        if len(mod_note_string) > 0:
            embed.add_field(
                name="Recent Mod Notes",
                value=mod_note_string,
                inline=False
            )
            if mod_notes_total > 25:
                embed.add_field(
                    name="Total Mod Notes",
                    value=f"Showing 25 of {mod_notes_total} total notes",
                )
            else:
                embed.add_field(
                    name="Total Mod Notes",
                    value=f"{mod_notes_total} total notes",
                )
        else:
            embed.add_field(
                name="Recent Mod Notes",
                value="No mod notes found",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ShowNotes(bot))