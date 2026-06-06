from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.cogs.commands.JE.progress import handle_award_progress
from src.config.awards import REPRESENT_MEDALS
from src.data.models import RepresentationPointMutation, RepresentationPoints
from src.data.repository.representation_repository import RepresentationRepository
from src.security import require_any_role, Role
from src.utils.embeds import default_embed, error_embed
from src.utils.representation_utils import get_current_representation_award, get_next_representation_award
from src.utils.time_utils import format_time, get_time_difference_past

log = getLogger(__name__)

_DEFAULT_HISTORY_LIMIT = 5
_MAX_HISTORY_LIMIT = 15


def _department_label(department) -> str:
    return department.value if department is not None else "Unknown"


def _format_mutation(mutation: RepresentationPointMutation) -> str:
    sign = "+" if mutation.points_delta > 0 else ""
    created_ago = format_time(get_time_difference_past(mutation.created_at))
    return (
        f"`{sign}{mutation.points_delta}` {_department_label(mutation.department)} "
        f"by <@{mutation.changed_by_id}> ({created_ago} ago)\n"
        f"> {mutation.reason}"
    )


def build_representation_embed(
        target: discord.Member,
        points_record: RepresentationPoints,
        mutations: list[RepresentationPointMutation],
) -> discord.Embed:
    total_points = points_record.total_representation_points
    current_award = get_current_representation_award(total_points)
    get_next_representation_award(total_points)

    embed = default_embed(
        title=f"Representation for {target.display_name}",
        description=target.mention,
        author=False,
    )
    embed.add_field(name="Total Points", value=str(total_points), inline=True)
    embed.add_field(
        name="Media / Scheduling",
        value=(
            f"{points_record.media_representation_points} / "
            f"{points_record.scheduling_representation_points}"
        ),
        inline=True,
    )
    embed.add_field(
        name="Current Badge",
        value=f"<@&{current_award.role_id}>" if current_award is not None else "None",
        inline=True,
    )

    if (
            total_points
            >= 0
    ):
        handle_award_progress(
            target,
            REPRESENT_MEDALS,
            embed,
            "Representation",
            total_points
        )

    if mutations:
        embed.add_field(
            name="Recent History",
            value="\n".join(_format_mutation(mutation) for mutation in mutations),
            inline=False,
        )
    else:
        embed.add_field(name="Recent History", value="No representation history found.", inline=False)

    return embed


class Representation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="representation",
        description="Show representation points and recent history for a member",
    )
    @app_commands.describe(
        target="Select the user you want to view",
        history_limit="How many recent history items to show",
    )
    @require_any_role(Role.JE)
    async def representation(
            self,
            interaction: discord.Interaction,
            target: discord.Member = None,
            history_limit: app_commands.Range[int, 1, _MAX_HISTORY_LIMIT] = _DEFAULT_HISTORY_LIMIT,
    ):
        if target is None:
            target = interaction.user

        await interaction.response.defer(ephemeral=False)

        repository = RepresentationRepository()
        try:
            points_record = repository.get_points_breakdown(target.id)
            mutations = repository.list_mutations(target.id, limit=history_limit)
            embed = build_representation_embed(target, points_record, mutations)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            log.error("Failed to display representation data: %s", e, exc_info=True)
            await interaction.followup.send(
                embed=error_embed(
                    title="Error",
                    description="Failed to load representation data.",
                ),
                ephemeral=True,
            )
        finally:
            repository.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(Representation(bot))
