from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config.awards import (
    CITATION_OF_COMBAT, COMBAT_MEDALS,
    CITATION_OF_CONDUCT, CONDUCT_MEDALS,
    NCO_IMPROVEMENT_RIBBON, FOUR_MONTHS_SERVICE_STRIPES,
    SERVICE_STRIPES, HONORABLE_CONDUCT,
    MARITIME_SERVICE_MEDAL, HOSTED_MEDALS
)
from src.config.main_server import GUILD_ID
from src.config.netc_server import (
    JLA_GRADUATE_ROLE, NETC_GRADUATE_ROLES,
    SNLA_GRADUATE_ROLE, OCS_GRADUATE_ROLE,
    SOCS_GRADUATE_ROLE, NETC_GUILD_ID
)
from src.config.ranks_roles import (
    SNCO_AND_UP, E3_ROLES, E2_ROLES,
    SPD_ROLES, O1_ROLES, O4_ROLES,
    O5_ROLES, MARINE_ROLE, JE_AND_UP
)
from src.data import Sailor, RoleChangeType
from src.data.repository.auditlog_repository import AuditLogRepository
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import SailorRepository, ensure_sailor_exists
from src.data.repository.voyage_repository import VoyageRepository
from src.data.structs import NavyRank
from src.utils.embeds import default_embed
from src.utils.rank_and_promotion_utils import (
    get_current_rank, get_rank_by_index,
    has_award_or_higher
)
from src.utils.ship_utils import get_ship_role_id_by_member

log = getLogger(__name__)

async def check_if_ship_valid_members(interaction: discord.Interaction, target_role: discord.Role) -> bool:
    members = target_role.members
    if not members:
        await interaction.followup.send("No members found in the specified role.")
        return False

    valid_members = False
    for member in members:
        if any(role.id in JE_AND_UP for role in member.roles):
            ensure_sailor_exists(member.id)
            valid_members = True

    if not valid_members:
        await interaction.followup.send("No eligible members found in the specified role.")
        return False

    return True

def meets_requirements(bot: commands.Bot, member: discord.Member, next_rank: NavyRank) -> bool:
    """
    Check if a member meets the requirements for their next rank.
    Uses audit logs to verify graduation roles.
    """
    audit_log_repository = AuditLogRepository()
    voyage_repository = VoyageRepository()

    try:
        # Get member roles from NETC server
        netc_guild = bot.get_guild(NETC_GUILD_ID)
        netc_member = netc_guild.get_member(member.id) if netc_guild else None
        netc_guild_member_role_ids = [role.id for role in netc_member.roles] if netc_member else []

        match next_rank.index:
            case 3:  # Able Seaman
                sailor_repository = SailorRepository()
                try:
                    sailor = sailor_repository.get_sailor(member.id)
                    voyage_count = sailor.voyage_count if sailor and sailor.voyage_count else 0
                finally:
                    sailor_repository.close_session()
                return (voyage_count >= 5 and
                        (has_award_or_higher(member, CITATION_OF_COMBAT, COMBAT_MEDALS) or
                         has_award_or_higher(member, CITATION_OF_CONDUCT, CONDUCT_MEDALS)))

            case 4:  # Junior Petty officer
                return (has_award_or_higher(member, NCO_IMPROVEMENT_RIBBON, [NCO_IMPROVEMENT_RIBBON]) and
                        has_award_or_higher(member, FOUR_MONTHS_SERVICE_STRIPES, SERVICE_STRIPES))

            case 5:  # Petty Officer
                return has_award_or_higher(member, HONORABLE_CONDUCT, CONDUCT_MEDALS)

            case 6:  # Chief Petty Officer
                return has_award_or_higher(member, MARITIME_SERVICE_MEDAL, HOSTED_MEDALS)

            case 7:  # Senior Chief Petty Officer
                hosted_repository = HostedRepository()
                try:
                    hosted_counts = hosted_repository.get_hosted_by_target_ids_month_count([member.id])
                    hosted_count = hosted_counts.get(member.id, 0)
                finally:
                    hosted_repository.close_session()
                return (hosted_count >= 5 and
                        has_award_or_higher(member, HOSTED_MEDALS[0], HOSTED_MEDALS))

            case 9:  # Midshipman
                has_graduate_role = False
                for role_id in NETC_GRADUATE_ROLES:
                    latest_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, role_id)
                    if not latest_role_log:
                        if role_id in netc_guild_member_role_ids:
                            has_graduate_role = True
                            break
                    elif latest_role_log.change_type == RoleChangeType.ADDED:
                        has_graduate_role = True
                        break
                return has_graduate_role

            case 10:  # Lieutenant
                latest_jla_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, JLA_GRADUATE_ROLE)
                if not latest_jla_role_log:
                    return JLA_GRADUATE_ROLE in netc_guild_member_role_ids
                return latest_jla_role_log.change_type == RoleChangeType.ADDED

            case 11:  # Lieutenant Commander
                latest_snla_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, SNLA_GRADUATE_ROLE)
                if not latest_snla_role_log:
                    return SNLA_GRADUATE_ROLE in netc_guild_member_role_ids
                return latest_snla_role_log.change_type == RoleChangeType.ADDED

            case 12:  # Commander
                latest_ocs_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, OCS_GRADUATE_ROLE)
                if not latest_ocs_role_log:
                    return OCS_GRADUATE_ROLE in netc_guild_member_role_ids
                return latest_ocs_role_log.change_type == RoleChangeType.ADDED

            case 13:  # Captain
                latest_socs_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, SOCS_GRADUATE_ROLE)
                if not latest_socs_role_log:
                    return SOCS_GRADUATE_ROLE in netc_guild_member_role_ids
                return latest_socs_role_log.change_type == RoleChangeType.ADDED

            case _:
                return False
    finally:
        audit_log_repository.close_session()
        voyage_repository.close_session()
class CheckShipPromotion(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="checkshippromotion", description="Check a whole ships promotion eligibility")
    @app_commands.checks.has_any_role(*SNCO_AND_UP)
    async def view_moderation(self, interaction: discord.Interaction, target: discord.Role = None):
        await interaction.response.defer(ephemeral=True)

        if target is None:
            sender_ship_role_id = get_ship_role_id_by_member(interaction.user)
            if sender_ship_role_id < 0:
                await interaction.followup.send("Please specify a ship role to check or join a ship.")
                return
            target = interaction.guild.get_role(sender_ship_role_id)
        if not target.name.startswith("USS"):
            await interaction.followup.send("The specified role is not a ship.")
            return

        if not await check_if_ship_valid_members(interaction, target):
            return

        members_status = []
        for member in target.members:
            if any(role.id in JE_AND_UP for role in member.roles):
                is_marine = MARINE_ROLE in [role.id for role in member.roles]

                current_rank = get_current_rank(member)
                if not current_rank:
                    continue

                next_rank = None
                for rank_index in current_rank.promotion_index:
                    next_rank = get_rank_by_index(rank_index)
                    if next_rank:
                        break

                if not next_rank:
                    continue

                current_rank_name = current_rank.name if not is_marine else current_rank.marine_name
                next_rank_name = next_rank.name if not is_marine else next_rank.marine_name

                eligible = "✅" if meets_requirements(self.bot, member, next_rank) else "❌"

                members_status.append(
                    f"{member.mention}: {current_rank_name} → {next_rank_name} {eligible}"
                )

        chunks = []
        current_chunk = []
        current_length = 0

        for status in members_status:
            status_length = len(status) + 1
            if current_length + status_length > 1024:
                chunks.append(current_chunk)
                current_chunk = [status]
                current_length = status_length
            else:
                current_chunk.append(status)
                current_length += status_length

        if current_chunk:
            chunks.append(current_chunk)

        for i, chunk in enumerate(chunks, 1):
            embed = default_embed(
                title=f"Ship Promotion Eligibility ({i}/{len(chunks)})",
                description=f"Checking promotion eligibility for {target.mention}",
                author=False
            )

            status_str = "\n".join(chunk)
            embed.add_field(
                name="Members Eligibility",
                value=status_str,
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(CheckShipPromotion(bot))
