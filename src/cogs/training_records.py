import discord
from discord import app_commands
from discord.ext import commands

from src.config.main_server import GUILD_ID
from src.config.netc_server import SNLA_GRADUATE_ROLE, NETC_GUILD_ID, JLA_GRADUATE_ROLE, OCS_GRADUATE_ROLE, \
    SOCS_GRADUATE_ROLE, SNLA_INSTRUCTOR_ROLE, JLA_INSTRUCTOR_ROLE, OCS_INSTRUCTOR_ROLE, SOCS_INSTRUCTOR_ROLE
from src.config.ranks_roles import JE_AND_UP, NETC_ROLE, NRC_ROLE
from src.data import TrainingRecord, member_report
from src.data.repository.training_records_repository import TrainingRecordsRepository
from src.utils.embeds import default_embed
from src.utils.time_utils import format_time, get_time_difference_past


class TrainingRecords(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="trainingrecords", description="Get information about a members training records")
    @app_commands.describe(target="Select the user you want to get information about")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def training_records(self, interaction: discord.interactions, target: discord.Member = None):
        if target is None:
            target = interaction.user

        # Get the training records of the target
        training_repository = TrainingRecordsRepository()
        training_record: TrainingRecord = training_repository.get_or_create_training_record(target.id)
        training_repository.close_session()

        embed = default_embed(
            title=f"Training Records",
            description=f"{target.mention}",
            author=False
        )

        # Attempt to set the thumbnail to the target's avatar
        try:
            avatar_url = target.guild_avatar.url if target.guild_avatar else target.avatar.url
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass

        relevant_departments = [self.bot.get_guild(GUILD_ID).get_role(role) for role in [NETC_ROLE, NRC_ROLE]]
        embed.add_field(
            name="Department",
            value=f"{ '\n'.join([role.mention for role in relevant_departments if role in target.roles]) or 'None'}",
        )
        embed.add_field(
            name="Training Points",
            value=f"{training_record.netc_training_points+training_record.nrc_training_points + training_record.st_training_points}",
        )
        # if user NRC and NETC Department member
        if NETC_ROLE in [role.id for role in target.roles] and NRC_ROLE in [role.id for role in target.roles]:
            embed.add_field(
                name="NRC / NETC Points",
                value=f"{training_record.nrc_training_points} / {training_record.netc_training_points}",
            )
        # if user is NRC Department member
        elif NETC_ROLE in [role.id for role in target.roles]:
            embed.add_field(
                name="NETC Points",
                value=f"{training_record.netc_training_points}",
            )
        # if user is NETC Department member
        elif NRC_ROLE in [role.id for role in target.roles]:
            embed.add_field(
                name="NRC Points",
                value=f"{training_record.nrc_training_points}",
            )
        else:
            embed.add_field(
                name="\u200b",
                value="\u200b",
            )

        netc_member = self.bot.get_guild(NETC_GUILD_ID).get_member(target.id)
        if netc_member is not None:
            embed.add_field(
                name="Time in NETC",
                value=f"{format_time(get_time_difference_past(netc_member.joined_at))}",
            )
            graduate_roles = [
                ("JLA", JLA_GRADUATE_ROLE),
                ("SNLA", SNLA_GRADUATE_ROLE),
                ("OCS", OCS_GRADUATE_ROLE),
                ("SOCS", SOCS_GRADUATE_ROLE)
            ]
            graduate_roles = [(name, role) for name, role in graduate_roles if role in [role.id for role in netc_member.roles]]
            if len(graduate_roles) > 0:
                embed.add_field(
                    name="Graduated for",
                    value="\n".join([f"- {name}" for name, role in graduate_roles]),
                    inline=True
                )
            instructor_roles = [
                ("JLA", JLA_INSTRUCTOR_ROLE),
                ("SNLA", SNLA_INSTRUCTOR_ROLE),
                ("OCS", OCS_INSTRUCTOR_ROLE),
                ("SOCS", SOCS_INSTRUCTOR_ROLE)
            ]
            instructor_roles = [(name, role) for name, role in instructor_roles if role in [role.id for role in netc_member.roles]]
            if len(instructor_roles) > 0:
                embed.add_field(
                    name="Instructor for",
                    value="\n".join([f"- {name}" for name, role in instructor_roles]),
                    inline=True
                )

        if training_record.nrc_training_points > 0 or training_record.st_training_points > 0:
            embed.add_field(
                name="NRC Points Breakdown:",
                value="\u200b",
                inline=False
            )
            if training_record.nrc_training_points > 0:
                embed.add_field(
                    name="Total NRC Points",
                    value=f"{training_record.nrc_training_points}",
                    inline=True
                )
            if training_record.st_training_points > 0:
                embed.add_field(
                    name="Total ST Points",
                    value=f"{training_record.st_training_points}",
                    inline=True
                )


        if not netc_member is None:
            netc_member_roles = [role.id for role in netc_member.roles]
            if any(role in netc_member_roles for role in [JLA_INSTRUCTOR_ROLE, SNLA_INSTRUCTOR_ROLE, OCS_INSTRUCTOR_ROLE, SOCS_INSTRUCTOR_ROLE]):
                embed.add_field(
                    name="\u200b",
                    value="\u200b",
                    inline=False
                )
                embed.add_field(
                    name="NETC Points Breakdown:",
                    value="\u200b",
                    inline=False
                )
            if training_record.jla_training_points > 0:
                embed.add_field(
                    name="Total JLA Points",
                    value=f"{training_record.jla_training_points}",
                    inline=True
                )
            if training_record.snla_training_points > 0:
                embed.add_field(
                    name="Total SNLA Points",
                    value=f"{training_record.snla_training_points}",
                    inline=True
                )
            if training_record.ocs_training_points > 0:
                embed.add_field(
                    name="Total OCS Points",
                    value=f"{training_record.ocs_training_points}",
                    inline=True
                )
            if training_record.socs_training_points > 0:
                embed.add_field(
                    name="SOCS Points",
                    value=f"{training_record.socs_training_points}",
                    inline=True
                )
            if training_record.nla_training_points > 0:
                embed.add_field(
                    name="Total NLA Points",
                    value=f"{training_record.nla_training_points}",
                    inline=True
                )
            if training_record.nla_training_points > 0:
                embed.add_field(
                    name="Total VLA Points",
                    value=f"{training_record.vla_training_points}",
                    inline=True
                )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TrainingRecords(bot))