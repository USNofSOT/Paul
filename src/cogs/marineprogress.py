from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands
from matplotlib.pyplot import title

from src.config.awards import COMBAT_MEDALS, MERITORIOUS_COMBAT_ACTION
from src.config.ranks_roles import JE_AND_UP
from src.config.subclasses import HELM_SUBCLASSES, CANNONEER_SUBCLASSES, FLEX_SUBCLASSES, \
    MASTER_FLEX, PRO_CANNONEER, PRO_HELM
from src.data.repository.sailor_repository import SailorRepository
from src.utils.embeds import member_embed, error_embed
from src.utils.rank_and_promotion_utils import get_current_award

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
    return f"{achieved_emoji * round(progress * length) + not_achieved_emoji * (length - round(progress * length))} {percentage}% ( {current}/{total} )"

class MarineProgress(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="marineprogress", description="Track your or another member's progress towards becoming a Marine.")
    @app_commands.describe(target="Select the user you want to get information about")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def progress(self, interaction: discord.Interaction, target: discord.Member = None):
        if target is None:
            target = interaction.user

        await interaction.response.defer(ephemeral=False)

        # Get sailor
        sailor_repository = SailorRepository()
        sailor = sailor_repository.get_sailor(target.id)
        sailor_repository.close_session()

        # Create initial embed
        embed=member_embed(target)
        embed.title = f"Marine Progress for {target.display_name}"

        def get_subclass_streak(target, subclasses):
            current_subclass = get_current_award(target, subclasses)
            return current_subclass.threshold if current_subclass is not None else 0

        # Master Flex Subclass
        current_flex_subclass_streak = get_subclass_streak(target, FLEX_SUBCLASSES)
        if current_flex_subclass_streak >= MASTER_FLEX.threshold:
            embed.add_field(
                name=f"**Flex Subclass**",
                value=f":white_check_mark: <@&{MASTER_FLEX.role_id}> achieved!",
                inline=False
            )
        else:
            embed.add_field(
                name=f"**Flex Subclass**",
                value=f"Requires: <@&{MASTER_FLEX.role_id}> \n {progres_bar(current_flex_subclass_streak, MASTER_FLEX.threshold)}",
                inline=False
            )

        # Pro Cannoneer or Pro Helm Subclass or higher
        current_helm_subclass_streak = get_subclass_streak(target, HELM_SUBCLASSES)
        current_cannoneer_subclass_streak = get_subclass_streak(target, CANNONEER_SUBCLASSES)
        if current_helm_subclass_streak >= PRO_HELM.threshold or current_cannoneer_subclass_streak >= PRO_CANNONEER.threshold:
            embed.add_field(
                name=f"**Pro Cannoneer or Helm Subclass**",
                value=f":white_check_mark: <@&{PRO_CANNONEER.role_id}> or <@&{PRO_HELM.role_id}> achieved!",
                inline=False
            )
        else:
            embed.add_field(
                name=f"**Pro Cannoneer or Helm Subclass**",
                value=f"Requires: <@&{PRO_CANNONEER.role_id}> or <@&{PRO_HELM.role_id}> \n {progres_bar(max(current_helm_subclass_streak, current_cannoneer_subclass_streak), PRO_HELM.threshold)}",
                inline=False
            )

        # Meritorious Combat Ribbon or higher
        current_highest_streak = get_subclass_streak(target, COMBAT_MEDALS)
        if current_highest_streak >= MERITORIOUS_COMBAT_ACTION.threshold:
            embed.add_field(
                name=f"**Meritorious Combat Ribbon or higher**",
                value=f":white_check_mark: <@&{MERITORIOUS_COMBAT_ACTION.role_id}> achieved!",
                inline=False
            )
        else:
            embed.add_field(
                name=f"**Meritorious Combat Ribbon or higher**",
                value=f"Requires: <@&{MERITORIOUS_COMBAT_ACTION.role_id}> \n {progres_bar(current_highest_streak, MERITORIOUS_COMBAT_ACTION.threshold)}",
                inline=False
            )

        embed.add_field(
            name="Additional Requirements",
            value="- Recommendation from Ship CO \n"
                  "- Going on a Skirmish with 2 members of the Marine Committee so they can determine the candidate's skill (can be one Skirmish with 2 Committee members, or 2 separate Skirmish voyage with a different Committee member each)"
        )

        await interaction.followup.send(embed=embed)

    @progress.error
    async def progress_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingAnyRole):
            await interaction.response.send_message(
                embed=error_embed(
                    title="Not Authorized",
                    description="You are not authorized to use this command.",
                )
            )
        else:
            await interaction.response.send_message(
                embed=error_embed(
                    title="Error",
                    description="An error occurred while processing the command.",
                )
            )
async def setup(bot: commands.Bot):
    await bot.add_cog(MarineProgress(bot))
