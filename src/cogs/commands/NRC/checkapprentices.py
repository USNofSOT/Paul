import logging

import discord
from discord import app_commands
from discord.ext import commands

from config.ranks import SEAMAN
from data.repository import voyage_repository
from src.data import RoleChangeType
import src.config.ranks
from src.config.emojis import NRC_EMOJI
from src.config.ranks_roles import apprentice_role
from src.security import require_any_role, Role

from src.data.repository.auditlog_repository import AuditLogRepository
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.data.models import Voyages

from sqlalchemy import func

from src.utils.time_utils import get_time_difference_in_days, utc_time_now
from src.utils.embeds import default_embed,error_embed
log = logging.getLogger(__name__)

class CheckApprentices(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="checkapprentices", description="View current Seaman Apprentices")
    @require_any_role(Role.NRC)
    async def checkapprentices(self,interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = default_embed(title=f"{NRC_EMOJI} Seaman Apprentices {NRC_EMOJI}", author=False)
        voyage_repository = VoyageRepository()
        now = utc_time_now()
        apprentices = []
        audit_log_repository = AuditLogRepository()
        sailor_repository = SailorRepository()
        apprentice_emoji = SEAMAN.emoji
        try:
            for member in interaction.guild.members:
                if apprentice_role not in (role.id for role in member.roles):
                    continue

                role_log = audit_log_repository.get_latest_role_log_for_target_and_role(
                    member.id,
                    apprentice_role,
                )
                returned_by = f"<@{role_log.changed_by_id}>" if role_log else "Unknown"

                days_as_apprentice = 0
                voyage_count = 0
                if role_log and role_log.change_type == RoleChangeType.ADDED:
                    days_as_apprentice = get_time_difference_in_days(now, role_log.log_time)
                    voyage_count = voyage_repository.get_voyage_after_log_roleadd(member.id, role_log.log_time)

                if voyage_count > 0:
                    has_voyaged = True
                else:
                    has_voyaged = False
                
                if has_voyaged:
                    status = ":white_check_mark: Add to Ship"
                elif days_as_apprentice >= 14:
                    status = ":warning: Revert to Deckhand"
                else:
                    status = f"{apprentice_emoji} Active"

                apprentices.append({
                    "member": member,
                    "has_voyaged": has_voyaged,
                    "days": days_as_apprentice,
                    "status": status,
                    "returned_by": returned_by,
                })
            # used to sort the apprentices, starting with anyone who might've voyaged, then sorts by most days active as an apprentice
            apprentices.sort(
                key=lambda apprentice: (
                    not apprentice["has_voyaged"],
                    -apprentice["days"],
                )
            )

            for apprentice in apprentices:
                voyaged = ":white_check_mark: Yes" if apprentice["has_voyaged"] else ":x: No"

                embed.add_field(
                    name=apprentice["member"].display_name,
                    value=(
                        f"{apprentice['member'].mention}\n"
                        f"Voyaged: {voyaged}\n"
                        f"Days as Apprentice: {apprentice['days']}\n"
                        f"Returned by: {apprentice['returned_by']}\n"
                        f"Status: {apprentice['status']}\n"
                    ),
                    inline=False,
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            log.error("Error occurred finding apprentices %s", e)
            return await interaction.followup.send(
                embed=error_embed(
                    description="An error occurred while finding apprentices",
                    exception=e,
                ),
                ephemeral=True,
            )
        finally:
            audit_log_repository.close_session()
            sailor_repository.close_session()
    @checkapprentices.error
    async def checkapprentices_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        log.error("Error occurred in checkapprentice command: %s", error)
        if isinstance(error, app_commands.errors.MissingAnyRole):
            embed = error_embed(
                title="Missing Permissions",
                description="You do not have the required permissions to use this command.",
                footer=False,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CheckApprentices(bot))

