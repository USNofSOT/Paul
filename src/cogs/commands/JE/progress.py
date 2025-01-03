from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config import NSC_ROLES
from src.config.awards import VOYAGE_MEDALS, HOSTED_MEDALS, TRAINING_MEDALS
from src.config.ranks_roles import NCO_AND_UP_PURE, NETC_ROLE, NRC_ROLE, JE_AND_UP
from src.config.subclasses import HELM_SUBCLASSES, CANNONEER_SUBCLASSES, CARPENTER_SUBCLASSES, FLEX_SUBCLASSES
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.training_records_repository import TrainingRecordsRepository
from src.data.structs import Award
from src.utils.embeds import member_embed, error_embed
from src.utils.rank_and_promotion_utils import get_current_award, get_next_award

log = getLogger(__name__)

def handle_award_progress(target: discord.Member, medal_list: [Award], embed: discord.Embed, medal_type: str, current_count: int):
    result_string = ""
    current_medal = get_current_award(target, medal_list)
    next_medal = get_next_award(target, medal_list)
    number_in_list = medal_list.index(current_medal) + 1 if current_medal else 0
    total_achievable_awards = len(medal_list)
    #previous_threshold = current_medal.threshold if current_medal else 0
    next_threshold = next_medal.threshold if next_medal else 0

    if next_medal:
        result_string = (
            f"Next {medal_type} Award: <@&{next_medal.role_id}>\n"
            f"> {progres_bar(current_count, next_threshold)} ({current_count}/{next_threshold}) "
        )
    else:
        result_string = f":white_check_mark: All {medal_type} Awards achieved!"

    if current_medal or current_medal is None and next_medal is medal_list[0]:
        embed.add_field(
            name=f"**{medal_type} Awards** ({number_in_list}/{total_achievable_awards})",
            value=result_string,
            inline=False
        )

def progres_bar(current, total):
    achieved_emoji = ":blue_square: "
    not_achieved_emoji = ":white_large_square: "
    full_achieved_emoji = ":green_square: "
    length = 10
    progress = min(current / total, 1)
    percentage = round(progress * 100)
    if progress == 1:
        return f"{full_achieved_emoji * length} {percentage}%"
    return f"{achieved_emoji * round(progress * length) + not_achieved_emoji * (length - round(progress * length))} {percentage}%"

class Progress(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="progress", description="Track your or another member's progress towards different awards")
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
        embed.title = f"Award progress for {target.display_name}"

        target_role_ids = [role.id for role in target.roles]

        # Voyage Awards
        handle_award_progress(target, VOYAGE_MEDALS, embed, "Voyage", sailor.voyage_count+sailor.force_voyage_count)
        if any(role_id in target_role_ids for role_id in NCO_AND_UP_PURE):
            handle_award_progress(target, HOSTED_MEDALS, embed, "Hosted", sailor.hosted_count+sailor.force_hosted_count)
        #handle_award_progress(target, SERVICE_STRIPES, embed, "Service Stripes", (discord.utils.utcnow() - target.joined_at).days // 30)

        handle_award_progress(target, CARPENTER_SUBCLASSES, embed, "Carpenter", sailor.carpenter_points+sailor.force_carpenter_points)
        handle_award_progress(target, FLEX_SUBCLASSES, embed, "Flex", sailor.flex_points+sailor.force_flex_points)
        handle_award_progress(target, CANNONEER_SUBCLASSES, embed, "Cannoneer", sailor.cannoneer_points+sailor.force_cannoneer_points)
        handle_award_progress(target, HELM_SUBCLASSES, embed, "Helm", sailor.helm_points+sailor.force_helm_points)

        if NRC_ROLE in target_role_ids or NETC_ROLE in target_role_ids:
            training_records_repository = TrainingRecordsRepository()
            training = training_records_repository.get_or_create_training_record(target.id)
            if training.nrc_training_points + training.netc_training_points + training.st_training_points >= 0:
                handle_award_progress(target, TRAINING_MEDALS, embed, "Training", training.nrc_training_points+training.netc_training_points + training.st_training_points)
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
    await bot.add_cog(Progress(bot))
