import discord
from discord import app_commands
from discord.ext import commands

from src.config import NSC_ROLE, SPD_NSC_ROLE
from src.config.main_server import GUILD_OWNER_ID, GUILD_ID
from src.config.ranks_roles import SNCO_AND_UP, BOA_ROLE
from src.data import Subclasses, SubclassType, RoleChangeLog, NameChangeLog, TimeoutLog, ModNotes
from src.data.repository.auditlog_repository import AuditLogRepository
from src.data.repository.modnote_repository import ModNoteRepository
from src.data.repository.subclass_repository import SubclassRepository
from src.data.structs import SailorCO
from src.utils.embeds import default_embed
from src.utils.time_utils import format_time, get_time_difference_past


class ViewModeration(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="viewmoderation", description="Moderation overview for a user")
    @app_commands.checks.has_any_role(*SNCO_AND_UP)
    async def view_moderation(self, interaction: discord.interactions, target: discord.Member = None):
        await interaction.response.defer(ephemeral=True)

        if target is None:
            target = interaction.user

        embed = default_embed(
            title=f"Moderation Overview",
            description=f"{target.mention}",
            author=False
        )
        try:
            avatar_url = target.guild_avatar.url if target.guild_avatar else target.avatar.url
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass

        embed.add_field(
            name="Time in Server",
            value=f"{format_time(get_time_difference_past(target.joined_at))}",
        )

        # Add Next in Command
        guild = self.bot.get_guild(GUILD_ID)
        co_str = SailorCO(target, guild).member_str
        embed.add_field(name="Next in Command", value=co_str, inline=True)

        embed.add_field(
            name="User ID",
            value=f"{target.id}"
        )

        subclass_repository = SubclassRepository()
        subclasses: [Subclasses] = subclass_repository.entries_for_target_id(target.id, 5)
        subclass_string = "\n".join(
            f"<@{subclass.author_id}> added `{subclass.subclass_count}x {SubclassType(subclass.subclass).name.capitalize()}` point(s) _({format_time(get_time_difference_past(subclass.log_time))} ago)_"
            for subclass in subclasses
        )
        if len(subclass_string) > 0:
            embed.add_field(
                name="Recent Subclass Changes",
                value=subclass_string,
                inline=False
            )
        subclass_repository.close_session()

        auditlog_repository = AuditLogRepository()
        role_changes: [RoleChangeLog] = auditlog_repository.get_role_changes_logs(target.id, 5)
        role_change_string = "\n".join(
            f"<@{role_change.changed_by_id}> `{role_change.change_type.name}` "
            f"{'<@&' + str(role_change.role_id) + '>' if target.guild.get_role(role_change.role_id) else f'{role_change.role_name} in `{self.bot.get_guild(role_change.guild_id).name}`'} "
            f"_({format_time(get_time_difference_past(role_change.log_time))} ago)_"
            for role_change in role_changes
        )
        if len(role_change_string) > 0:
            embed.add_field(
                name="Recent Role Changes",
                value=role_change_string,
                inline=True
            )

        name_changes: [NameChangeLog] = auditlog_repository.get_name_changes_logs(target.id, 5, guild_id=GUILD_ID)
        name_change_string = "\n".join(
            f"<@{name_change.changed_by_id}> changed name from `{name_change.name_before}` to `{name_change.name_after}` _({format_time(get_time_difference_past(name_change.log_time))} ago)_"
            for name_change in name_changes
        )
        if len(name_change_string) > 0:
            embed.add_field(
                name="Recent Name Changes (USN Server)",
                value=name_change_string,
                inline=False
            )

        timeout_changes: [TimeoutLog] = auditlog_repository.get_timeout_logs(target.id, 5)
        timeout_change_string = "\n".join(
            #   f"**Timed out for {timeout_change.length}** \n -#by <@{timeout_change.changed_by_id}> at {format_time(get_time_difference_past(timeout_change.log_time))}"
            f"<@{timeout_change.changed_by_id}> set timeout to `{timeout_change.length}` _({format_time(get_time_difference_past(timeout_change.log_time))} ago)_"
            for timeout_change in timeout_changes
        )

        if len(timeout_change_string) > 0:
            embed.add_field(
                name="Recent Timeouts",
                value=timeout_change_string,
                inline=False
            )
        auditlog_repository.close_session()

        mod_note_repository = ModNoteRepository()
        interaction_user_roles = [role.id for role in interaction.user.roles]
        is_boa = BOA_ROLE in interaction_user_roles

        mod_notes: [ModNotes] = mod_note_repository.get_modnotes(target_id=target.id, limit=5, show_hidden=is_boa)
        mod_notes_total: int = mod_note_repository.count_modnotes(target.id, include_hidden=is_boa)
        mod_note_string = "\n".join(
            f"{mod_note.id}: <@{mod_note.moderator_id}>: {mod_note.note} _({format_time(get_time_difference_past(mod_note.note_time))} ago)_{' (`HIDDEN`)' if mod_note.hidden else ''}"
            for mod_note in mod_notes
        )
        if len(mod_note_string) > 0:
            embed.add_field(
                name="Recent Mod Notes",
                value=mod_note_string,
                inline=False
            )
        if mod_notes_total > 5:
            embed.add_field(
                name="Total Mod Notes",
                value=f"{mod_notes_total} total notes \n \n run the command `/shownotes` to see up to 25 notes",
            )

        await interaction.followup.send(embed=embed, ephemeral=True)




async def setup(bot: commands.Bot):
    await bot.add_cog(ViewModeration(bot))