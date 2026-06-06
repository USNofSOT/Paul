from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.cogs.commands.JE.representation import build_representation_embed
from src.config.representation import (
    HEAD_OF_MEDIA_ROLE_ID,
    HEAD_OF_SCHEDULING_ROLE_ID,
    MEDIA_REPRESENTATION_MANAGER_ROLE_IDS,
    SCHEDULING_REPRESENTATION_MANAGER_ROLE_IDS,
)
from src.data.models import RepresentationDepartment
from src.data.repository.representation_repository import RepresentationRepository
from src.security import Role, resolve_effective_roles
from src.utils.embeds import error_embed
from src.utils.representation_utils import (
    can_add_representation_points,
    can_remove_representation_points,
    can_view_representation_mod,
)

log = getLogger(__name__)

_DEFAULT_HISTORY_LIMIT = 10
_MAX_HISTORY_LIMIT = 20


class RepresentationMod(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="representationmod",
        description="Add, remove, or review representation points for a member",
    )
    @app_commands.describe(
        target="Select the user you want to manage",
        department="Which department the points belong to",
        add="Add this many points",
        remove="Remove this many points",
        reason="Why this action is being taken",
        history_limit="How many history items to show",
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
            history_limit: app_commands.Range[int, 1, _MAX_HISTORY_LIMIT] = _DEFAULT_HISTORY_LIMIT,
    ):
        await interaction.response.defer(ephemeral=False)

        interaction_role_ids = {role.id for role in interaction.user.roles}
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

        if add is not None and remove is not None:
            await interaction.followup.send(
                embed=error_embed(
                    title="Invalid Input",
                    description="Use either `add` or `remove`, not both.",
                ),
                ephemeral=True,
            )
            return

        if (add is not None or remove is not None) and department is None:
            await interaction.followup.send(
                embed=error_embed(
                    title="Missing Department",
                    description="You must choose a department when adding or removing points.",
                ),
                ephemeral=True,
            )
            return

        if (add is not None or remove is not None) and not reason:
            await interaction.followup.send(
                embed=error_embed(
                    title="Missing Reason",
                    description="A reason is required when adding or removing points.",
                ),
                ephemeral=True,
            )
            return

        repository = RepresentationRepository()
        try:
            if add is not None or remove is not None:
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
            mutations = repository.list_mutations(target.id, limit=history_limit)
            embed = build_representation_embed(target, points_record, mutations)
            if add is not None:
                embed.title = f"Representation updated for {target.display_name}"
                embed.add_field(
                    name="Action",
                    value=f"Added `{add}` {_department_label(RepresentationDepartment(department))} point(s).",
                    inline=False,
                )
            elif remove is not None:
                embed.title = f"Representation updated for {target.display_name}"
                embed.add_field(
                    name="Action",
                    value=f"Removed `{remove}` {_department_label(RepresentationDepartment(department))} point(s).",
                    inline=False,
                )
            else:
                embed.title = f"Representation moderation view for {target.display_name}"

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


async def setup(bot: commands.Bot):
    await bot.add_cog(RepresentationMod(bot))
