from enum import member

import discord
from discord import app_commands
from discord.ext import commands

from src.config.awards import CITATION_OF_COMBAT, COMBAT_MEDALS, CITATION_OF_CONDUCT, CONDUCT_MEDALS
from src.config.main_server import GUILD_ID
from src.config.netc_server import JLA_GRADUATE_ROLE, NETC_GRADUATE_ROLES
from src.config.ranks_roles import JE_AND_UP, E3_ROLES, E2_ROLES
from src.data import Sailor, RoleChangeType
from src.data.repository.auditlog_repository import AuditLogRepository
from src.data.repository.sailor_repository import SailorRepository, ensure_sailor_exists
from src.data.repository.voyage_repository import VoyageRepository
from src.data.structs import NavyRank
from src.utils.embeds import default_embed
from src.utils.rank_and_promotion_utils import get_current_rank, get_rank_by_index, has_award_or_higher
from src.utils.time_utils import get_time_difference_in_days, utc_time_now, format_time, get_time_difference


class CheckPromotion(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="checkpromotion", description="Check promotion eligibility")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def view_moderation(self, interaction: discord.interactions, target: discord.Member = None):
        if target is None:
            target = interaction.user

        ensure_sailor_exists(target.id)
        audit_log_repository = AuditLogRepository()
        voyage_repository = VoyageRepository()

        # Get information from member from guild
        guild_member = self.bot.get_guild(GUILD_ID).get_member(target.id)
        guild_member_role_ids = [role.id for role in guild_member.roles]
        netc_guild_member = self.bot.get_guild(GUILD_ID).get_member(target.id)
        netc_guild_member_role_ids = [role.id for role in netc_guild_member.roles]

        # Get user information as sailor from database
        sailor_repository = SailorRepository()
        sailor: Sailor = sailor_repository.get_sailor(target.id)
        sailor_repository.close_session()

        # Get voyage count
        voyage_count: int = sailor.voyage_count + sailor.force_voyage_count or 0

        embed = default_embed(
            title=f"{target.display_name or target.name}",
            description=f"{target.mention}",
            author=False
        )
        try:
            avatar_url = guild_member.guild_avatar.url if guild_member.guild_avatar else guild_member.avatar.url
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass
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

                    # if user is seaman apprentice
                    if E2_ROLES[1] in guild_member_role_ids:
                        latest_voyage = voyage_repository.get_last_voyage_by_target_ids([target.id])
                        if latest_voyage:
                            voyage_time = latest_voyage[target.id]
                            days_since_voyage = get_time_difference_in_days(utc_time_now(), voyage_time)
                            if days_since_voyage <= 14:
                                requirements += f":white_check_mark: Had a voyage in the last 14 days ({format_time(get_time_difference(utc_time_now(), voyage_time))} ago) \n"
                            else:
                                requirements += f":x: Had a voyage in the last 14 days ({format_time(get_time_difference(utc_time_now(), voyage_time))} ago) \n"
                    else:
                        ### Prerequisites ###
                        ## Complete 5 total voyages ##
                        if voyage_count > 5:
                            requirements += f":white_check_mark: Go on five voyages ({voyage_count}/5) \n"
                        else:
                            requirements += f":x: Go on five voyages ({voyage_count}/5) \n"

                        ## Citation of Combat OR Citation of Conduct ##
                        if (has_award_or_higher(guild_member,CITATION_OF_COMBAT,COMBAT_MEDALS)
                        or has_award_or_higher(guild_member,CITATION_OF_CONDUCT,CONDUCT_MEDALS)):
                            requirements += f":white_check_mark: Awarded <@&{CITATION_OF_CONDUCT.role_id}> or <@&{CITATION_OF_COMBAT.role_id}> \n"
                        else:
                            requirements += f":x: Awarded <@&{CITATION_OF_CONDUCT.role_id}> or <@&{CITATION_OF_COMBAT.role_id}> \n"
                case 4: # Junior Petty Officer

                    ### Prerequisites ###

                    ## Complete 15 total voyages and wait 2 week as an E-3 or Complete 20 total voyages and wait 1 week as an E-3 ##
                    latest_e3_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(target.id, E3_ROLES[0])

                    days_with_e3 = get_time_difference_in_days(utc_time_now(), latest_e3_role_log.log_time) if latest_e3_role_log else None
                    if days_with_e3 is None or latest_e3_role_log.change_type != RoleChangeType.ADDED:
                        days_with_e3 = 0

                    if voyage_count >= 15 and days_with_e3 >= 14:
                        requirements += f":white_check_mark: Go on fifteen voyages ({voyage_count}/15) and wait two weeks as an E-3 ({days_with_e3}/14) \n"
                    elif voyage_count >= 20 and days_with_e3 >= 7:
                        requirements += f":white_check_mark: Go on twenty voyages ({voyage_count}/20)  and wait one week as an E-3 ({days_with_e3}/7) \n"
                    else:
                        requirements += f":x: Go on fifteen voyages ({voyage_count}/15) and wait two weeks as an E-3 ({days_with_e3}/14) \n"
                        requirements += "**OR**\n"
                        requirements += f":x: Go on twenty voyages ({voyage_count}/20)  and wait one week as an E-3 ({days_with_e3}/7) \n"
                        requirements += f"**AND**\n"

                    ## JLA ##
                    if JLA_GRADUATE_ROLE in netc_guild_member_role_ids:
                        requirements += f":white_check_mark: is a JLA Graduate \n"
                    else:
                        requirements += f":x: is a JLA Graduate \n"



                    ## Citation of Conduct ##
                    if has_award_or_higher(guild_member,CITATION_OF_CONDUCT,CONDUCT_MEDALS):
                        requirements += f":white_check_mark: Awarded <@&{CITATION_OF_CONDUCT.role_id}> \n"
                    else:
                        requirements += f":x: Awarded <@&{CITATION_OF_CONDUCT.role_id}> \n"

            if len(requirements) > 0:
                embed.add_field(
                    name=f"Promotion Requirements - {next_rank.name}",
                    value=f"{requirements}",
                    inline=False
                )
            additional_requirements = next_rank.rank_prerequisites.additional_requirements if next_rank.rank_prerequisites else []
            if len(additional_requirements) > 0:
                embed.add_field(
                    name=f"Additional Requirements",
                    value="\n".join(additional_requirements),
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=False)
        audit_log_repository.close_session()
        voyage_repository.close_session()

async def setup(bot: commands.Bot):
    await bot.add_cog(CheckPromotion(bot))