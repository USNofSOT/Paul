import discord
from discord import app_commands
from discord.ext import commands

from src.config.main_server import GUILD_ID
from src.config.netc_server import NETC_GUILD_ID
from src.config.ranks_roles import E2_ROLES, JE_AND_UP, MARINE_ROLE
from src.data import Sailor
from src.data.repository.auditlog_repository import AuditLogRepository
from src.data.repository.sailor_repository import SailorRepository, ensure_sailor_exists
from src.data.repository.voyage_repository import VoyageRepository
from src.data.structs import NavyRank
from src.utils.embeds import default_embed
from src.utils.promotion import build_default_promotion_check_service
from src.utils.promotion.models import PromotionContext
from src.utils.rank_and_promotion_utils import get_current_rank


class CheckPromotion(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.promotion_service = build_default_promotion_check_service()

    @app_commands.command(name="checkpromotion", description="Check promotion eligibility")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def view_moderation(
            self,
            interaction: discord.Interaction,
            target: discord.Member = None,
    ):
        if target is None:
            target = interaction.user

        ensure_sailor_exists(target.id)
        audit_log_repository = AuditLogRepository()
        voyage_repository = VoyageRepository()

        try:
            guild_member = self.bot.get_guild(GUILD_ID).get_member(target.id)
            guild_member_role_ids = {role.id for role in guild_member.roles}

            netc_guild_member = self.bot.get_guild(NETC_GUILD_ID).get_member(target.id)
            netc_guild_member_role_ids = (
                {role.id for role in netc_guild_member.roles}
                if netc_guild_member
                else set()
            )

            is_marine = MARINE_ROLE in guild_member_role_ids

            sailor_repository = SailorRepository()
            try:
                sailor: Sailor = sailor_repository.get_sailor(target.id)
            finally:
                sailor_repository.close_session()

            voyage_count = sailor.voyage_count + sailor.force_voyage_count or 0
            hosted_count = sailor.hosted_count + sailor.force_hosted_count or 0

            embed = default_embed(
                title=f"{target.display_name or target.name}",
                description=f"{target.mention}",
                author=False,
            )
            try:
                avatar_url = (
                    guild_member.guild_avatar.url
                    if guild_member.guild_avatar
                    else guild_member.avatar.url
                )
                embed.set_thumbnail(url=avatar_url)
            except AttributeError:
                pass

            current_rank: NavyRank = get_current_rank(guild_member)
            if current_rank is None:
                embed.add_field(name="Current Rank", value="No rank found")
                await interaction.response.send_message(embed=embed, ephemeral=False)
                return

            current_rank_name = current_rank.marine_name if is_marine else current_rank.name
            if E2_ROLES[1] in guild_member_role_ids:
                current_rank_name = "Seaman Apprentice"

            embed.add_field(name="Current Rank", value=current_rank_name)

            context = PromotionContext(
                guild_member=guild_member,
                guild_member_role_ids=guild_member_role_ids,
                netc_guild_member_role_ids=netc_guild_member_role_ids,
                target_id=target.id,
                voyage_count=voyage_count,
                hosted_count=hosted_count,
                current_rank=current_rank,
                is_marine=is_marine,
                audit_log_repository=audit_log_repository,
                voyage_repository=voyage_repository,
            )

            rendered_sections = self.promotion_service.evaluate(context)
            for rendered_section in rendered_sections:
                for field in rendered_section.fields:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)
                if rendered_section.show_or_separator_after and len(rendered_sections) > 1:
                    embed.add_field(name="\u200b", value="**OR** \n \u200b")

            if any(section.has_required_failures for section in rendered_sections):
                embed.colour = discord.Colour.red()
            elif any(section.has_required_information for section in rendered_sections):
                embed.colour = discord.Colour.blue()
            elif any(section.has_required_successes for section in rendered_sections):
                embed.colour = discord.Colour.green()
            else:
                embed.colour = discord.Colour.blue()

            await interaction.response.send_message(embed=embed, ephemeral=False)
        finally:
            audit_log_repository.close_session()
            voyage_repository.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(CheckPromotion(bot))
