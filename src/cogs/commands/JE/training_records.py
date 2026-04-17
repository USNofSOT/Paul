import discord
from discord import app_commands
from discord.ext import commands

from src.cogs.commands.JE.progress import handle_award_progress
from src.config.awards import TRAINING_MEDALS
from src.config.main_server import GUILD_ID
from src.config.netc_server import (
    NETC_ACTIVE_CURRICULUMS,
    NETC_GUILD_ID,
    NETC_LEGACY_CURRICULUMS,
)
from src.config.ranks_roles import NETC_ROLE, NRC_ROLE
from src.data import TrainingRecord
from src.data.repository.training_records_repository import TrainingRecordsRepository
from src.security import require_any_role, Role
from src.utils.embeds import default_embed
from src.utils.time_utils import format_time, get_time_difference_past

ACTIVE_NETC_POINT_FIELDS = (
    ("jla_training_points", "Total JLA Points"),
    ("sla_training_points", "Total SLA Points"),
    ("cosa_training_points", "Total COSA Points"),
    ("ocs_training_points", "Total OCS Points"),
    ("socs_training_points", "SOCS Points"),
)
LEGACY_TRAINING_POINT_FIELDS = (
    ("snla_training_points", "Total SNLA Points"),
    ("nla_training_points", "Total NLA Points"),
    ("vla_training_points", "Total VLA Points"),
)


def _curricula_for_graduate_roles(
        member_role_ids: set[int], curricula: tuple[tuple[str, int, int, int], ...]
) -> list[str]:
    return [
        name for name, _, _, graduate_role in curricula if graduate_role in member_role_ids
    ]


def _curricula_for_instructor_roles(
        member_role_ids: set[int], curricula: tuple[tuple[str, int, int, int], ...]
) -> list[str]:
    return [
        name
        for name, _, instructor_role, _ in curricula
        if instructor_role in member_role_ids
    ]


def _get_positive_point_fields(
        training_record: TrainingRecord, point_fields: tuple[tuple[str, str], ...]
) -> list[tuple[str, int]]:
    return [
        (label, points)
        for attribute_name, label in point_fields
        if (points := getattr(training_record, attribute_name, 0)) > 0
    ]


def _format_curriculum_list(curricula: list[str]) -> str:
    return "\n".join(f"- {name}" for name in curricula)


def _add_breakdown_fields(
        embed: discord.Embed,
        title: str,
        point_fields: list[tuple[str, int]],
) -> None:
    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(name=title, value="\u200b", inline=False)
    for label, points in point_fields:
        embed.add_field(name=label, value=f"{points}", inline=True)


class TrainingRecords(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="trainingrecords",
        description="Get information about a members training records",
    )
    @app_commands.describe(target="Select the user you want to get information about")
    @require_any_role(Role.JE, Role.NETC_HIGH_COMMAND)
    async def training_records(
        self, interaction: discord.interactions, target: discord.Member = None
    ):
        if target is None:
            target = interaction.user

        # Get the training records of the target
        training_repository = TrainingRecordsRepository()
        training_record: TrainingRecord = (
            training_repository.get_or_create_training_record(target.id)
        )
        training_repository.close_session()

        embed = default_embed(
            title="Training Records", description=f"{target.mention}", author=False
        )

        # Attempt to set the thumbnail to the target's avatar
        try:
            avatar_url = (
                target.guild_avatar.url if target.guild_avatar else target.avatar.url
            )
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass

        target_role_ids = {role.id for role in target.roles}
        main_guild = self.bot.get_guild(GUILD_ID)
        relevant_departments = []
        if main_guild is not None:
            relevant_departments = [
                role
                for role in (
                    main_guild.get_role(NETC_ROLE),
                    main_guild.get_role(NRC_ROLE),
                )
                if role is not None
            ]
        department_mentions = "\n".join(
            [role.mention for role in relevant_departments if role.id in target_role_ids]
        )
        embed.add_field(
            name="Department",
            value=department_mentions or "None",
        )
        embed.add_field(
            name="Training Points",
            value=f"{training_record.netc_training_points+training_record.nrc_training_points + training_record.st_training_points}",
        )
        # if user NRC and NETC Department member
        if NETC_ROLE in target_role_ids and NRC_ROLE in target_role_ids:
            embed.add_field(
                name="NRC / NETC Points",
                value=f"{training_record.nrc_training_points + training_record.st_training_points} / {training_record.netc_training_points}",
            )
        # if user is NRC Department member
        elif NETC_ROLE in target_role_ids:
            embed.add_field(
                name="NETC Points",
                value=f"{training_record.netc_training_points}",
            )
        # if user is NETC Department member
        elif NRC_ROLE in target_role_ids:
            embed.add_field(
                name="NRC Points",
                value=f"{training_record.nrc_training_points + training_record.st_training_points}",
            )
        else:
            embed.add_field(
                name="\u200b",
                value="\u200b",
            )

        netc_guild = self.bot.get_guild(NETC_GUILD_ID)
        netc_member = netc_guild.get_member(target.id) if netc_guild is not None else None
        if netc_member is not None:
            netc_member_role_ids = {role.id for role in netc_member.roles}
            embed.add_field(
                name="Time in NETC",
                value=f"{format_time(get_time_difference_past(netc_member.joined_at))}",
            )
            active_graduate_curricula = _curricula_for_graduate_roles(
                netc_member_role_ids, NETC_ACTIVE_CURRICULUMS
            )
            legacy_graduate_curricula = _curricula_for_graduate_roles(
                netc_member_role_ids, NETC_LEGACY_CURRICULUMS
            )
            active_instructor_curricula = _curricula_for_instructor_roles(
                netc_member_role_ids, NETC_ACTIVE_CURRICULUMS
            )
            legacy_instructor_curricula = _curricula_for_instructor_roles(
                netc_member_role_ids, NETC_LEGACY_CURRICULUMS
            )

            if len(active_graduate_curricula) > 0:
                embed.add_field(
                    name="Graduated for",
                    value=_format_curriculum_list(active_graduate_curricula + legacy_graduate_curricula),
                    inline=True,
                )
            if len(active_instructor_curricula) > 0:
                embed.add_field(
                    name="Instructor for",
                    value=_format_curriculum_list(active_instructor_curricula + legacy_instructor_curricula),
                    inline=True,
                )

        else:
            active_instructor_curricula = []
            legacy_instructor_curricula = []

        if (
            training_record.nrc_training_points > 0
            or training_record.st_training_points > 0
        ):
            embed.add_field(name="NRC Points Breakdown:", value="\u200b", inline=False)
            if training_record.nrc_training_points > 0:
                embed.add_field(
                    name="Total RT Points",
                    value=f"{training_record.nrc_training_points}",
                    inline=True,
                )
            if training_record.st_training_points > 0:
                embed.add_field(
                    name="Total ST Points",
                    value=f"{training_record.st_training_points}",
                    inline=True,
                )

        active_point_fields = _get_positive_point_fields(
            training_record, ACTIVE_NETC_POINT_FIELDS
        )
        legacy_point_fields = _get_positive_point_fields(
            training_record, LEGACY_TRAINING_POINT_FIELDS
        )
        if len(active_point_fields) > 0 or len(active_instructor_curricula) > 0:
            _add_breakdown_fields(embed, "NETC Points Breakdown:", active_point_fields)
        if len(legacy_point_fields) > 0 or len(legacy_instructor_curricula) > 0:
            _add_breakdown_fields(
                embed, "Legacy Training Breakdown:", legacy_point_fields
            )

        embed.add_field(name="\u200b", value="\u200b", inline=False)

        if (
            training_record.nrc_training_points
            + training_record.netc_training_points
            + training_record.st_training_points
            >= 0
        ):
            handle_award_progress(
                target,
                TRAINING_MEDALS,
                embed,
                "Training",
                training_record.nrc_training_points
                + training_record.netc_training_points
                + training_record.st_training_points,
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(TrainingRecords(bot))
