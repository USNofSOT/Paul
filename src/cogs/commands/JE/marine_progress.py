from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from config import MARINE_ROLE, USMC_ROLE
from data import RoleChangeType
from data.repository.auditlog_repository import AuditLogRepository
from src.config.awards import COMBAT_MEDALS, MERITORIOUS_COMBAT_ACTION
from src.config.ranks_roles import JE_AND_UP
from src.config.subclasses import (
    CANNONEER_SUBCLASSES,
    CARPENTER_SUBCLASSES,
    FLEX_SUBCLASSES,
    HELM_SUBCLASSES,
)
from src.utils.embeds import error_embed, member_embed
from src.utils.rank_and_promotion_utils import get_current_award, has_award_or_higher
from utils.time_utils import format_time, get_time_difference_past

log = getLogger(__name__)


def progres_bar(current, total):
    achieved_emoji = ":blue_square: "
    not_achieved_emoji = ":white_large_square: "
    full_achieved_emoji = ":green_square: "
    length = 10
    progress = min(current / total, 1)
    percentage = round(progress * 100)
    if progress == 1:
        return f"{full_achieved_emoji * length} {percentage}% ( {current}/{total} )"
    return f"{
        achieved_emoji * round(progress * length)
        + not_achieved_emoji * (length - round(progress * length))
    } {percentage}% ( {current}/{total} )"


class MarineProgress(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="marineprogress",
        description="Track your or another member's progress "
        "towards becoming a Marine.",
    )
    @app_commands.describe(target="Select the user you want to get information about")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def progress(
        self, interaction: discord.Interaction, target: discord.Member = None
    ):
        if target is None:
            target = interaction.user

        await interaction.response.defer(ephemeral=False)

        is_marine = MARINE_ROLE in [role.id for role in target.roles]
        is_usmc = USMC_ROLE in [role.id for role in target.roles]
        audit_log_repository = AuditLogRepository()

        latest_marine_role_log = (
            audit_log_repository.get_latest_role_log_for_target_and_role(
                target.id, MARINE_ROLE
            )
        )

        latest_usmc_role_log = (
            audit_log_repository.get_latest_role_log_for_target_and_role(
                target.id, USMC_ROLE
            )
        )

        audit_log_repository.close_session()

        if (
            latest_marine_role_log
            and latest_marine_role_log.change_type == RoleChangeType.REMOVED
        ):
            latest_marine_role_log = None

        if (
            latest_usmc_role_log
            and latest_usmc_role_log.change_type == RoleChangeType.REMOVED
        ):
            latest_usmc_role_log = None

        # Create initial embed
        embed = member_embed(target)
        embed.title = f"Marine Progress for {target.display_name}"

        if is_marine:
            if not latest_marine_role_log:
                embed.add_field(name="Marine Status", value=":white_check_mark: Marine")
            else:
                embed.add_field(
                    name="Marine Status",
                    value=f":white_check_mark: Marine for "
                    f"{format_time(get_time_difference_past(latest_marine_role_log.log_time))}",
                )

            if is_usmc:
                if not latest_usmc_role_log:
                    embed.add_field(name="USMC Status", value=":white_check_mark: USMC")
                else:
                    embed.add_field(
                        name="USMC Status",
                        value=f":white_check_mark: USMC for "
                        f"{format_time(get_time_difference_past(latest_usmc_role_log.log_time))}",
                    )

            return await interaction.followup.send(embed=embed)

        def get_subclass_streak(target, subclasses):
            current_subclass = get_current_award(target, subclasses)
            return (
                current_subclass.threshold
                if current_subclass and current_subclass.threshold is not None
                else 0
            )

        ADEPT_INDEX = 0
        PRO_INDEX = 1

        SUBCLASSES = {
            "cannoneer": CANNONEER_SUBCLASSES,
            "carpenter": CARPENTER_SUBCLASSES,
            "helm": HELM_SUBCLASSES,
            "flex": FLEX_SUBCLASSES,
        }

        adept_count = sum(
            has_award_or_higher(target, subclass[ADEPT_INDEX], subclass) or 0
            for subclass in SUBCLASSES.values()
        )
        pro_count = sum(
            has_award_or_higher(target, subclass[PRO_INDEX], subclass) or 0
            for subclass in SUBCLASSES.values()
        )

        # Require 2 Pro subclasses
        if pro_count < 2:
            embed.add_field(
                name="Pro subclasses",
                value=f"Requires 2 Pro subclasses \n > {progres_bar(pro_count, 2)}",
                inline=False,
            )
        else:
            embed.add_field(
                name="Pro subclasses",
                value=f":white_check_mark: You have {pro_count}/2 Pro subclasses.",
                inline=False,
            )

        # Require 4 Adept subclasses
        if adept_count < 4:
            embed.add_field(
                name="Adept subclasses",
                value=f"Requires 4 Adept subclasses \n > {progres_bar(adept_count, 4)}",
                inline=False,
            )
            progres_bar(adept_count, 4)
        else:
            embed.add_field(
                name="Adept subclasses",
                value=f":white_check_mark: You have {adept_count}/4 Adept subclasses.",
                inline=False,
            )

        # Meritorious Combat Ribbon or higher
        current_highest_streak = get_subclass_streak(target, COMBAT_MEDALS)
        if current_highest_streak >= MERITORIOUS_COMBAT_ACTION.threshold:
            embed.add_field(
                name="**Meritorious Combat Ribbon or higher**",
                value=f":white_check_mark: "
                f"<@&{MERITORIOUS_COMBAT_ACTION.role_id}> achieved!",
                inline=False,
            )
        else:
            embed.add_field(
                name="**Meritorious Combat Ribbon or higher**",
                value=f"Requires: <@&{MERITORIOUS_COMBAT_ACTION.role_id}> \n "
                f"> {
                    progres_bar(
                        current_highest_streak, MERITORIOUS_COMBAT_ACTION.threshold
                    )
                }",
                inline=False,
            )

        embed.add_field(
            name="Additional Requirements",
            value="- An extensive recommendation from a Marine member \n"
            "- Going on a Skirmish with 2 members of the Marine Committee "
            "so they can determine the candidate's skill "
            "\n \t - A minimum of 2 separate Skirmish voyages is required "
            "\n \t - Each evaluation must be done by a different "
            "Marine Committee member",
        )

        await interaction.followup.send(embed=embed)

    @progress.error
    async def progress_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingAnyRole):
            await interaction.followup.send(
                embed=error_embed(
                    title="Not Authorized",
                    description="You are not authorized to use this command.",
                )
            )
        else:
            log.error("Error processing command: %s", error)
            await interaction.followup.send(
                embed=error_embed(
                    title="Error",
                    description="An error occurred while processing the command.",
                )
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(MarineProgress(bot))
