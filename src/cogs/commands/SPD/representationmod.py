from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config.representation import (
    HEAD_OF_MEDIA_ROLE_ID,
    HEAD_OF_SCHEDULING_ROLE_ID,
    MEDIA_REPRESENTATION_MANAGER_ROLE_IDS,
    SCHEDULING_REPRESENTATION_MANAGER_ROLE_IDS,
)
from src.config.spd_servers import SPD_GUILD_ID
from src.data.models import RepresentationDepartment
from src.data.repository.representation_repository import RepresentationRepository
from src.security import Role, resolve_effective_roles
from src.utils.embeds import default_embed, error_embed
from src.utils.representation_utils import (
    can_add_representation_points,
    can_remove_representation_points,
    can_view_representation_mod,
)

log = getLogger(__name__)


class RepresentationMod(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="representationmod",
        description="Add or remove representation points for a member",
    )
    @app_commands.describe(
        target="Select the user you want to manage",
        department="Which department the points belong to",
        add="Add this many points",
        remove="Remove this many points",
        reason="Why this action is being taken",
    )
    @app_commands.choices(
        department=[
            app_commands.Choice(name="Media", value=RepresentationDepartment.MEDIA.value),
            app_commands.Choice(name="Scheduling", value=RepresentationDepartment.SCHEDULING.value),
        ]
    )
    async def representationmod(
            self,
            interaction: discord.Interaction,
            target: discord.Member,
            department: str = None,
            add: app_commands.Range[int, 1, 100] = None,
            remove: app_commands.Range[int, 1, 100] = None,
            reason: str = None,
    ):
        await interaction.response.defer(ephemeral=False)

        interaction_role_ids = get_representation_actor_role_ids(
            interaction.user,
            self._get_spd_member(interaction.user.id),
        )
        effective_roles = resolve_effective_roles(interaction.user)
        if not can_view_representation_mod(interaction_role_ids, effective_roles):
            await interaction.followup.send(
                embed=error_embed(
                    title="Not Authorized",
                    description="You are not authorized to use this command.",
                ),
                ephemeral=True,
            )
            return

        validation_error = validate_representation_mutation_request(
            add=add,
            remove=remove,
            department=department,
            reason=reason,
        )
        if validation_error is not None:
            await interaction.followup.send(
                embed=error_embed(
                    title=validation_error[0],
                    description=validation_error[1],
                ),
                ephemeral=True,
            )
            return

        repository = RepresentationRepository()
        try:
            department_enum = RepresentationDepartment(department)
            if add is not None and not can_add_representation_points(
                    interaction_role_ids,
                    effective_roles,
                    department_enum,
            ):
                await interaction.followup.send(
                    embed=error_embed(
                        title="Not Authorized",
                        description=self._unauthorized_add_message(department_enum),
                    ),
                    ephemeral=True,
                )
                return

            if remove is not None and not can_remove_representation_points(
                    interaction_role_ids,
                    effective_roles,
                    department_enum,
            ):
                await interaction.followup.send(
                    embed=error_embed(
                        title="Not Authorized",
                        description=self._unauthorized_remove_message(department_enum),
                    ),
                    ephemeral=True,
                )
                return

            if add is not None:
                repository.add_points(
                    target_id=target.id,
                    changed_by_id=interaction.user.id,
                    department=department_enum,
                    amount=add,
                    reason=reason,
                )
            else:
                repository.remove_points(
                    target_id=target.id,
                    changed_by_id=interaction.user.id,
                    department=department_enum,
                    amount=remove,
                    reason=reason,
                )

            points_record = repository.get_points_breakdown(target.id)
            if add is not None:
                embed = build_representation_mod_result_embed(
                    target=target,
                    actor=interaction.user,
                    action=f"Added `{add}` {_department_label(RepresentationDepartment(department))} point(s).",
                    new_total_count=points_record.total_representation_points,
                )
            elif remove is not None:
                embed = build_representation_mod_result_embed(
                    target=target,
                    actor=interaction.user,
                    action=f"Removed `{remove}` {_department_label(RepresentationDepartment(department))} point(s).",
                    new_total_count=points_record.total_representation_points,
                )

            await interaction.followup.send(embed=embed)
        except ValueError as e:
            await interaction.followup.send(
                embed=error_embed(
                    title="Invalid Request",
                    description=str(e),
                ),
                ephemeral=True,
            )
        except Exception as e:
            log.error("Failed to manage representation data: %s", e, exc_info=True)
            await interaction.followup.send(
                embed=error_embed(
                    title="Error",
                    description="Failed to manage representation data.",
                ),
                ephemeral=True,
            )
        finally:
            repository.close_session()

    def _get_spd_member(self, user_id: int) -> discord.Member | None:
        spd_guild = self.bot.get_guild(SPD_GUILD_ID)
        if spd_guild is None:
            return None
        return spd_guild.get_member(user_id)

    def _unauthorized_add_message(self, department: RepresentationDepartment) -> str:
        if department == RepresentationDepartment.MEDIA:
            allowed_roles = ", ".join(f"<@&{role_id}>" for role_id in MEDIA_REPRESENTATION_MANAGER_ROLE_IDS)
        else:
            allowed_roles = ", ".join(f"<@&{role_id}>" for role_id in SCHEDULING_REPRESENTATION_MANAGER_ROLE_IDS)
        return (
            f"You are not authorized to add {department.value} representation points. "
            f"Allowed roles: {allowed_roles}, or users with `{Role.BOA}` / `{Role.NSC_ADMINISTRATOR}`."
        )

    def _unauthorized_remove_message(self, department: RepresentationDepartment) -> str:
        if department == RepresentationDepartment.MEDIA:
            allowed_roles = f"<@&{HEAD_OF_MEDIA_ROLE_ID}>"
        else:
            allowed_roles = f"<@&{HEAD_OF_SCHEDULING_ROLE_ID}>"
        return (
            f"You are not authorized to remove {department.value} representation points. "
            f"Allowed roles: {allowed_roles}, or users with `{Role.BOA}` / `{Role.NSC_ADMINISTRATOR}`."
        )


def _department_label(department: RepresentationDepartment) -> str:
    return department.value


def validate_representation_mutation_request(
        *,
        add: int | None,
        remove: int | None,
        department: str | None,
        reason: str | None,
) -> tuple[str, str] | None:
    if add is None and remove is None:
        return "Missing Action", "Use either `add` or `remove` to modify representation points."
    if add is not None and remove is not None:
        return "Invalid Input", "Use either `add` or `remove`, not both."
    if department is None:
        return "Missing Department", "You must choose a department when adding or removing points."
    if not reason:
        return "Missing Reason", "A reason is required when adding or removing points."
    return None


def build_representation_mod_result_embed(
        *,
        target: discord.Member,
        actor: discord.Member | discord.User,
        action: str,
        new_total_count: int,
) -> discord.Embed:
    embed = default_embed(
        title=f"Representation updated for {target.display_name}",
        description=target.mention,
        author=False,
    )
    embed.add_field(name="Action", value=action, inline=False)
    embed.add_field(name="Updated By", value=actor.mention, inline=False)
    embed.add_field(name="New Total Count", value=str(new_total_count), inline=False)
    return embed


def get_representation_actor_role_ids(
        interaction_member: discord.Member,
        spd_member: discord.Member | None = None,
) -> set[int]:
    role_ids = {role.id for role in interaction_member.roles}
    if spd_member is not None:
        role_ids.update(role.id for role in spd_member.roles)
    return role_ids


async def setup(bot: commands.Bot):
    await bot.add_cog(RepresentationMod(bot))
