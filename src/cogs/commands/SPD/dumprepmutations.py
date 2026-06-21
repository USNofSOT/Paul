from __future__ import annotations

import csv
import io
from logging import getLogger

import discord
from discord.ext import commands

from src.config.spd_servers import SPD_GUILD_ID
from src.data.models import RepresentationDepartment, RepresentationPointMutation, RepresentationPoints
from src.data.repository.representation_repository import RepresentationRepository
from src.security import resolve_effective_roles
from src.utils.embeds import error_embed
from src.utils.representation_utils import can_remove_representation_points

log = getLogger(__name__)


def normalize_representation_dump_department(
        department: str | None,
) -> RepresentationDepartment | None:
    if department is None:
        return None

    normalized_department = department.strip().lower()
    if normalized_department == "media":
        return RepresentationDepartment.MEDIA
    if normalized_department == "scheduling":
        return RepresentationDepartment.SCHEDULING
    raise ValueError("Department must be `Media` or `Scheduling`.")


def build_representation_dump_csv(
        points_records: list[RepresentationPoints],
        mutations: list[RepresentationPointMutation],
) -> str:
    buffer = io.StringIO()

    points_writer = csv.writer(buffer, lineterminator="\n")
    points_writer.writerow(["[POINT_TOTALS]"])
    points_writer.writerow(
        ["target_id", "media_representation_points", "scheduling_representation_points", "total_representation_points"]
    )
    for record in points_records:
        points_writer.writerow([
            record.target_id,
            record.media_representation_points,
            record.scheduling_representation_points,
            record.total_representation_points,
        ])

    points_writer.writerow([])
    points_writer.writerow(["[MUTATIONS]"])
    points_writer.writerow(
        ["id", "target_id", "changed_by_id", "department", "points_delta", "reason", "created_at"]
    )
    for mutation in mutations:
        points_writer.writerow([
            mutation.id,
            mutation.target_id,
            mutation.changed_by_id,
            mutation.department.value,
            mutation.points_delta,
            mutation.reason,
            mutation.created_at,
        ])

    return buffer.getvalue()


class DumpRepresentationMutations(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="dumprepmutations")
    async def dump_representation_mutations(
            self,
            ctx: commands.Context,
            department: str | None = None,
    ) -> None:
        actor_role_ids = get_representation_actor_role_ids(
            ctx.author,
            self._get_spd_member(ctx.author.id),
        )
        effective_roles = resolve_effective_roles(ctx.author)

        if not (
                can_remove_representation_points(actor_role_ids, effective_roles, RepresentationDepartment.MEDIA)
                or can_remove_representation_points(actor_role_ids, effective_roles,
                                                    RepresentationDepartment.SCHEDULING)
        ):
            await ctx.send(
                embed=error_embed(
                    title="Not Authorized",
                    description="Only department heads may dump representation data.",
                )
            )
            return

        repository = RepresentationRepository()
        try:
            department_filter = normalize_representation_dump_department(department)
            points_records = _filter_points_records_by_department(
                repository.list_all_points(),
                department_filter,
            )
            mutations = repository.list_all_mutations(department=department_filter)

            csv_text = build_representation_dump_csv(points_records, mutations)
            csv_file = discord.File(
                io.BytesIO(csv_text.encode("utf-8")),
                filename="repmutations.csv",
            )
            try:
                await ctx.author.send(
                    content="Your representation data export is attached.",
                    file=csv_file,
                )
            except discord.Forbidden:
                await ctx.send(
                    embed=error_embed(
                        title="DM Failed",
                        description="I could not DM you the export file. Please enable direct messages and try again.",
                    )
                )
                return

            await ctx.send("I sent the representation export to your DMs.")
        except ValueError as error:
            await ctx.send(
                embed=error_embed(
                    title="Invalid Request",
                    description=str(error),
                )
            )
        except Exception as error:
            log.error("Failed to dump representation mutations: %s", error, exc_info=True)
            await ctx.send(
                embed=error_embed(
                    title="Error",
                    description="Failed to dump representation data.",
                )
            )
        finally:
            repository.close_session()

    def _get_spd_member(self, user_id: int) -> discord.Member | None:
        spd_guild = self.bot.get_guild(SPD_GUILD_ID)
        if spd_guild is None:
            return None
        return spd_guild.get_member(user_id)


def get_representation_actor_role_ids(
        interaction_member: discord.Member,
        spd_member: discord.Member | None = None,
) -> set[int]:
    role_ids = {role.id for role in interaction_member.roles}
    if spd_member is not None:
        role_ids.update(role.id for role in spd_member.roles)
    return role_ids


def _filter_points_records_by_department(
        points_records: list[RepresentationPoints],
        department: RepresentationDepartment | None,
) -> list[RepresentationPoints]:
    if department is None:
        return points_records
    if department == RepresentationDepartment.MEDIA:
        return [record for record in points_records if record.media_representation_points > 0]
    return [record for record in points_records if record.scheduling_representation_points > 0]


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DumpRepresentationMutations(bot))
