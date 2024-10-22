import discord
from discord import app_commands
from discord.ext import commands

from src.config.awards import CITATION_OF_COMBAT, COMBAT_MEDALS, CITATION_OF_CONDUCT, CONDUCT_MEDALS
from src.config.main_server import GUILD_ID
from src.config.ranks_roles import JE_AND_UP
from src.data import Sailor
from src.data.repository.sailor_repository import SailorRepository
from src.data.structs import NavyRank
from src.utils.embeds import default_embed
from src.utils.rank_and_promotion_utils import get_current_rank, get_rank_by_index, has_award_or_higher


class CheckPromotion(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="checkpromotion", description="Check promotion eligibility")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def view_moderation(self, interaction: discord.interactions, target: discord.Member = None):
        if target is None:
            target = interaction.user

        # Get information from member from guild
        guild_member = self.bot.get_guild(GUILD_ID).get_member(target.id)
        guild_member_role_ids = [role.id for role in guild_member.roles]

        # Get user information as sailor from database
        sailor_repository = SailorRepository()
        sailor: Sailor = sailor_repository.get_sailor(target.id)
        sailor_repository.close_session()

        embed = default_embed(
            title=f"{target.display_name or target.name}",
            description=f"{target.mention}",
            author=False
        )
        current_rank: NavyRank = get_current_rank(guild_member)
        embed.add_field(
            name="Current Rank",
            value=f"{current_rank.name}",
        )


        for rank_index in current_rank.promotion_index:
            next_rank = get_rank_by_index(rank_index)

            requirements=""
            additional_requirements=[]
            match next_rank.index:
                case 3: # Able Seaman

                    ### Prerequisites ###
                    ## Complete 5 total voyages ##
                    voyage_count: int = sailor.voyage_count + sailor.force_voyage_count or 0
                    if voyage_count > 5:
                        requirements += f":white_check_mark: Go on five voyages ({voyage_count}/5)"
                    else:
                        requirements += f":x: Go on five voyages ({voyage_count}/5)"

                    ## Citation of Combat OR Citation of Conduct ##
                    if (has_award_or_higher(guild_member,CITATION_OF_COMBAT,COMBAT_MEDALS)
                    or has_award_or_higher(guild_member,CITATION_OF_CONDUCT,CONDUCT_MEDALS)):
                        requirements += f"\n:white_check_mark: <@&{CITATION_OF_CONDUCT.role_id}> or <@&{CITATION_OF_COMBAT.role_id}>"
                    else:
                        requirements += f"\n:x: <@&{CITATION_OF_CONDUCT.role_id}> or <@&{CITATION_OF_COMBAT.role_id}>"

            if len(requirements) > 0:
                embed.add_field(
                    name=f"Promotion Requirements",
                    value=f"{requirements}",
                    inline=False
                )
            if len(next_rank.rank_prerequisites.additional_requirements) > 0:
                embed.add_field(
                    name=f"Additional Requirements",
                    value="\n".join(next_rank.rank_prerequisites.additional_requirements),
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(CheckPromotion(bot))