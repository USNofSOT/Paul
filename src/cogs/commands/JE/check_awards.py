import logging

import discord
from discord import app_commands
from discord.ext import commands

from src.briefings.daily import render_pending_award_embeds
from src.briefings.message import chunk_discord_embeds
from src.config import GUILD_ID
from src.data.repository.ship_briefing_repository import ShipBriefingRepository
from src.security import Role, require_any_role
from src.utils.check_awards import get_pending_ship_awards
from src.utils.embeds import error_embed

log = logging.getLogger(__name__)


class CheckAwards(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="check_awards",
        description="Check award eligibility for a member or role.",
    )
    @app_commands.guild_only()
    @require_any_role(Role.JE)
    @app_commands.describe(target="Member or role to check.")
    async def check_awards(
        self,
        interaction: discord.Interaction,
        target: discord.Member | discord.Role,
    ) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        members = target.members if isinstance(target, discord.Role) else [target]
        member_ids = [member.id for member in members]
        repository = ShipBriefingRepository()
        try:
            guild = interaction.guild or self.bot.get_guild(GUILD_ID)
            if guild is None:
                raise LookupError("Award-check guild is unavailable.")

            sailors = {
                sailor.discord_id: sailor
                for sailor in repository.get_sailors_by_ids(member_ids)
            }
            subject_name = (
                target.name
                if isinstance(target, discord.Role)
                else target.display_name
            )
            if sailors:
                public_service_counts = repository.get_public_service_counts(
                    member_ids
                )
                pending_awards = tuple(
                    award
                    for member in members
                    if (sailor := sailors.get(member.id)) is not None
                    for award in get_pending_ship_awards(
                        guild,
                        sailor,
                        member,
                        public_service_count=public_service_counts.get(
                            member.id,
                            0,
                        ),
                    )
                )
                embeds = render_pending_award_embeds(
                    pending_awards,
                    subject_name=subject_name,
                )
            else:
                embeds = (
                    discord.Embed(
                        title=f"Awards · {subject_name}",
                        description=(
                            "No tracked sailors were found for this selection, "
                            "so award eligibility could not be evaluated."
                        ),
                        color=discord.Color.orange(),
                    ),
                )
            allowed_mentions = discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False,
            )
            for embed_page in chunk_discord_embeds(embeds):
                await interaction.followup.send(
                    embeds=list(embed_page),
                    ephemeral=True,
                    allowed_mentions=allowed_mentions,
                )
        except Exception:
            log.exception("Award eligibility check failed.")
            await interaction.followup.send(
                embed=error_embed(
                    title="Award check failed",
                    description=(
                        "The award check failed and the error has been logged."
                    ),
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        finally:
            repository.close_session()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CheckAwards(bot))
