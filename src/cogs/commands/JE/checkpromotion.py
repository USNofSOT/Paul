from dis import disco
from enum import member
import asyncio
from typing import Union

import discord
from discord import Interaction, app_commands, Role, ButtonStyle, SelectOption  
from discord.ext import commands
from discord.ui import Button, View, Select  
import io

from src.config.awards import CITATION_OF_COMBAT, COMBAT_MEDALS, CITATION_OF_CONDUCT, CONDUCT_MEDALS, \
    NCO_IMPROVEMENT_RIBBON, FOUR_MONTHS_SERVICE_STRIPES, SERVICE_STRIPES, HONORABLE_CONDUCT, MARITIME_SERVICE_MEDAL, \
    HOSTED_MEDALS
from src.config.main_server import GUILD_ID
from src.config.netc_server import JLA_GRADUATE_ROLE, NETC_GRADUATE_ROLES, SNLA_GRADUATE_ROLE, OCS_GRADUATE_ROLE, \
    SOCS_GRADUATE_ROLE, NETC_GUILD_ID
from src.config.ranks_roles import JE_AND_UP, E3_ROLES, E6_ROLES, E2_ROLES, SPD_ROLES, O1_ROLES, O4_ROLES, O5_ROLES, MARINE_ROLE, \
    E7_ROLES, E1_ROLES, E4_ROLES, E5_ROLES, E8_ROLES, O2_ROLES, O3_ROLES, O6_ROLES, O7_ROLES, O8_ROLES
from src.config.ranks import RANKS
from src.data import Sailor, RoleChangeType
from src.data.repository.auditlog_repository import AuditLogRepository
from src.data.repository.sailor_repository import SailorRepository, ensure_sailor_exists
from src.data.repository.voyage_repository import VoyageRepository
from src.data.structs import NavyRank
from src.utils.embeds import default_embed
from src.utils.rank_and_promotion_utils import get_current_rank, get_rank_by_index, has_award_or_higher
from src.utils.time_utils import get_time_difference_in_days, utc_time_now, format_time, get_time_difference
from src.utils.ship_utils import get_ship_role_id_by_member, get_ship_by_role_id


DISALLOWED_ROLES = [
    "Junior Enlisted",
    "Civilian"
]

RANK_EMOJIS = {
    'Seaman | E-2': '<:E2:1245860781887590472>',
    'Able Seaman | E-3': '<:E3:1245860807980617848>',
    'Junior Petty Officer | E-4': '<:E4:1245860835138605066>',
    'Petty Officer | E-6': '<:E6:1245860878142799923>',
    'Chief Petty Officer | E-7': '<:E7:1245860900162769016>',
    'Senior Chief Petty Officer | E-8': '<:E8:1245860921470091367>',
    'Midshipman | O-1': '<:O1:1245860986640928789>',
    'Lieutenant | O-3': '<:O3:1245861011265814620>',
    'Lieutenant Commander | O-4': '<:O4:1245861035542315149>',
    'Commander | O-5': '<:O5:1245861052554678365>',
    'Captain | O-6': '<:O6:1245861070950633574>',
    'Commodore | O-7': '<:O7:1245861091029024840>',
    'Rear Admiral | O-8': '<:O8:1245861113330008065>'
}

def is_role_disallowed(role_name):
    """Check if a role is in the disallowed list or doesn't match required patterns."""
    if role_name in DISALLOWED_ROLES:
        return True
    if not (role_name.startswith("USS") or role_name.endswith("Squad")):
        return True
    return False

def get_squad_role_id_by_member(member: discord.Member) -> int:
    """Get the squad role ID for a member"""
    if not member:
        return -2
    for role in member.roles:
        if role.name.endswith('Squad'):
            return role.id
    return -1

class CounterButton(discord.ui.Button):
    def __init__(self, current, total):
        super().__init__(
            label=f"Page {current + 1}/{total}",
            style=ButtonStyle.gray,
            disabled=True
        )

class MemberSelect(Select):
    def __init__(self, members):
        options = [
            SelectOption(
                label=member.display_name[:25], 
                value=str(member.id),
                description=f"View details for {member.display_name[:25]}"
            ) for member in members
        ]
        super().__init__(placeholder="Select a member...", options=options)

    async def callback(self, interaction: discord.Interaction):
        member = interaction.guild.get_member(int(self.values[0]))
        view = self.view
        if view.detailed:
            embed = await view.create_detailed_embed(member)
            await interaction.response.edit_message(embed=embed)

class PromotionView(View):
    def __init__(self, sailors, detailed=False, bot=None):  
        super().__init__(timeout=600)  
        self.sailors = sailors
        self.current_page = 0
        self.detailed = detailed
        self.per_page = 1 if detailed else 9
        self.pages = [self.sailors[i:i + self.per_page] for i in range(0, len(self.sailors), self.per_page)] if sailors else []
        self.bot = bot  

        if len(self.pages) > 1:
            self.add_item(PreviousButton())
            self.add_item(CounterButton(self.current_page, len(self.pages)))
            self.add_item(NextButton())
        
        if len(sailors) > 1:
            self.add_item(MemberSelect(sailors))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        
        try:
            await self.message.edit(view=self)
        except:
            pass

    def get_embed(self):  
        if not self.pages:
            return discord.Embed(title="Promotion Status", description="No members to display", color=discord.Color.blue())

        if not self.detailed:
            embed = discord.Embed(title="Promotion Status", description="Summary grid view", color=discord.Color.blue())
            return embed

        return None  

    async def create_detailed_embed(self, member):
        cog = self.bot.get_cog('CheckPromotion')
        if not cog:
            return discord.Embed(title="Error", description="Could not find CheckPromotion cog", color=discord.Color.red())
            
        is_eligible, requirements, embed = await cog.check_single_promotion_status(member, None)
        return embed

    async def send_initial_message(self, interaction: discord.Interaction):
        if self.detailed:
            if self.pages:
                embed = await self.create_detailed_embed(self.pages[self.current_page][0])
            else:
                embed = discord.Embed(title="Error", description="No members to display", color=discord.Color.red())
        else:
            embed = self.get_embed()
        
        response = await interaction.response.send_message(embed=embed, view=self)
        self.message = await interaction.original_response()

    async def update_counter(self):
        for item in self.children:
            if isinstance(item, CounterButton):
                item.label = f"Page {self.current_page + 1}/{len(self.pages)}"
                break

class PreviousButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Previous", style=ButtonStyle.secondary) 

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.current_page > 0:
            view.current_page -= 1
            await view.update_counter()
            if view.detailed:
                embed = await view.create_detailed_embed(view.pages[view.current_page][0])
            else:
                embed = view.get_embed()
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.defer()

class NextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Next", style=ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.current_page < len(view.pages) - 1:
            view.current_page += 1
            await view.update_counter()
            if view.detailed:
                embed = await view.create_detailed_embed(view.pages[view.current_page][0])
            else:
                embed = view.get_embed()
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.defer()

class SummaryView(View):
    def __init__(self, all_members, eligible_members, bot):
        super().__init__(timeout=600) 
        self.all_members = all_members
        self.eligible_members = eligible_members
        self.bot = bot

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        
        try:
            await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(label="Show All", style=ButtonStyle.primary)
    async def send_all(self, interaction: discord.Interaction, button: Button):
        view = PromotionView(self.all_members, detailed=True, bot=self.bot)
        if view.pages:
            embed = await view.create_detailed_embed(view.pages[0][0])
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()
        else:
            await interaction.response.send_message("No members to display", ephemeral=True)

    @discord.ui.button(label="Show Eligible", style=ButtonStyle.success)
    async def send_eligible(self, interaction: discord.Interaction, button: Button):
        view = PromotionView(self.eligible_members, detailed=True, bot=self.bot)
        if view.pages:
            embed = await view.create_detailed_embed(view.pages[0][0])
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()
        else:
            await interaction.response.send_message("No eligible members to display", ephemeral=True)

ENABLE_PERMISSION_CHECKS = True  # Set to False to disable role/ship permission checks for testing

class CheckPromotion(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def handle_role_check(self, interaction: discord.Interaction, role: discord.Role):
        """Handle checking promotion status for all members with a specific role."""
        members_with_role = [
            member for member in interaction.guild.members 
            if role in member.roles
        ]

        if not members_with_role:
            await interaction.response.send_message(
                f"No members found with the role {role.name}.", ephemeral=True
            )
            return

        initial_embed = discord.Embed(
            title=f"Promotion Status for {role.name}",
            description=f"Getting promotion status for members with the role {role.mention}...\n\nThere are {len(members_with_role)} members with this role. Please stand by for the results.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=initial_embed)
        
        stats = {
            'total_members': len(members_with_role),
            'eligible_count': 0,
            'rank_breakdown': {},
            'all_members': [],
            'eligible_members': []
        }

        for member in members_with_role:
            is_eligible, requirements, embed = await self.check_single_promotion_status(member, None)
            current_rank = self.get_member_rank(member)
            
            if current_rank not in stats['rank_breakdown']:
                stats['rank_breakdown'][current_rank] = {
                    'total': 0,
                    'eligible': 0
                }
            
            stats['rank_breakdown'][current_rank]['total'] += 1
            stats['all_members'].append(member)
            
            if is_eligible:
                stats['eligible_count'] += 1
                stats['rank_breakdown'][current_rank]['eligible'] += 1
                stats['eligible_members'].append(member)

        summary_embed = discord.Embed(
            title=f"Promotion Status Summary for {role.name}",
            description=f"Total Members: {stats['total_members']}\nEligible for Promotion: {stats['eligible_count']}\n\n",
            color=discord.Color.blue()
        )

        rank_order = [
            'Seaman Apprentice | E-2',
            'Seaman | E-2',
            'Able Seaman | E-3',
            'Junior Petty Officer | E-4',
            'Petty Officer | E-6',
            'Chief Petty Officer | E-7',
            'Senior Chief Petty Officer | E-8',
            'Midshipman | O-1',
            'Lieutenant | O-3',
            'Lieutenant Commander | O-4',
            'Commander | O-5',
            'Captain | O-6',
            'Commodore | O-7',
            'Rear Admiral | O-8'
        ]
        for rank_name in rank_order:
            if rank_name in stats['rank_breakdown']:
                data = stats['rank_breakdown'][rank_name]
                rank_emoji = RANK_EMOJIS.get(rank_name, "")
                percentage = (data['eligible'] / data['total'] * 100) if data['total'] > 0 else 0
                summary_embed.add_field(
                    name=f"{rank_emoji} {rank_name.split('|')[0].strip()}",
                    value=f"Total: {data['total']}\nEligible: {data['eligible']} ({percentage:.1f}%)",
                    inline=True
                )

        promotion_rate = (stats['eligible_count'] / stats['total_members'] * 100) if stats['total_members'] > 0 else 0
        summary_embed.add_field(
            name="Overall Statistics",
            value=f"Promotion Rate: {promotion_rate:.1f}%\nTotal Eligible: {stats['eligible_count']}/{stats['total_members']}",
            inline=False
        )

        view = SummaryView(stats['all_members'], stats['eligible_members'], self.bot)
        await interaction.edit_original_response(embed=summary_embed, view=view)

    def get_member_rank(self, member):
        """Get the member's current rank based on roles."""
        member_roles = [role.id for role in member.roles]
        
        rank_roles = {
            'Rear Admiral | O-8': O8_ROLES,
            'Commodore | O-7': O7_ROLES,
            'Captain | O-6': O6_ROLES,
            'Commander | O-5': O5_ROLES,
            'Lieutenant Commander | O-4': O4_ROLES,
            'Lieutenant | O-3': O3_ROLES, 
            'Midshipman | O-1': O1_ROLES,
            'Senior Chief Petty Officer | E-8': E8_ROLES,
            'Chief Petty Officer | E-7': E7_ROLES,
            'Petty Officer | E-6': E6_ROLES,
            'Junior Petty Officer | E-4': E4_ROLES,
            'Able Seaman | E-3': E3_ROLES,
            'Seaman | E-2': E2_ROLES[0:1],  # Exclude Seaman Apprentice
            'Seaman Apprentice | E-2': E2_ROLES[1:2]  # Only Seaman Apprentice
        }

        for rank_name, role_ids in rank_roles.items():
            if any(role_id in member_roles for role_id in role_ids):
                return rank_name
        return "Unknown"

    @app_commands.command(name="checkpromotion", description="Check promotion eligibility for a member or role")
    @app_commands.describe(target="The member or role to check")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def checkpromotion(self, interaction: discord.Interaction, target: Union[discord.Member, discord.Role]):
        """Check promotion eligibility for a member or role"""
        if isinstance(target, discord.Role):
            if not (target.name.startswith("USS") or target.name.endswith("Squad")):
                await interaction.response.send_message(
                    "The role must be either a ship or squad.", ephemeral=True
                )
                return

            if ENABLE_PERMISSION_CHECKS:
                has_high_rank = any(role.id in O5_ROLES for role in interaction.user.roles)
                
                if not has_high_rank:
                    has_required_rank = any(role.id in [*E6_ROLES, *O4_ROLES] for role in interaction.user.roles)
                    if not has_required_rank:
                        await interaction.response.send_message(
                            "You must be at least E-6 to run ship/squad reports.", ephemeral=True
                        )
                        return

                    user_ship_id = get_ship_role_id_by_member(interaction.user)
                    user_squad_id = get_squad_role_id_by_member(interaction.user)
                    
                    if target.id != user_ship_id and target.id != user_squad_id:
                        await interaction.response.send_message(
                            "You can only check promotion status for your own ship/squad.", ephemeral=True
                        )
                        return

            await self.handle_role_check(interaction, target)
        else:
            await interaction.response.defer()
            try:
                is_eligible, requirements, embed = await self.check_single_promotion_status(target, interaction)
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(
                    f"An error occurred while checking promotion status: {str(e)}", 
                    ephemeral=True
                )

    async def create_promotion_embed(self, member, is_eligible, requirements):
        embed = discord.Embed(
            title=f"{member.display_name or member.name}",
            description=f"{member.mention}",
            color=discord.Color.blue()
        )
        try:
            avatar_url = member.guild_avatar.url if member.guild_avatar else member.avatar.url
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass

        embed.add_field(
            name="Promotion Status",
            value="Eligible" if is_eligible else "Not Eligible",
            inline=False
        )
        embed.add_field(
            name="Requirements",
            value=requirements,
            inline=False
        )

        return embed

    async def check_single_promotion_status(self, member, interaction: discord.Interaction = None):
        ensure_sailor_exists(member.id)
        audit_log_repository = AuditLogRepository()
        voyage_repository = VoyageRepository()

        guild_member = self.bot.get_guild(GUILD_ID).get_member(member.id)
        guild_member_role_ids = [role.id for role in guild_member.roles]
        netc_guild_member = self.bot.get_guild(NETC_GUILD_ID).get_member(member.id)
        netc_guild_member_role_ids = [role.id for role in netc_guild_member.roles] if netc_guild_member else []

        is_eligible = False

        is_marine = MARINE_ROLE in guild_member_role_ids

        sailor_repository = SailorRepository()
        sailor: Sailor = sailor_repository.get_sailor(member.id)
        sailor_repository.close_session()

        voyage_count: int = sailor.voyage_count + sailor.force_voyage_count or 0
        hosted_count: int = sailor.hosted_count + sailor.force_hosted_count or 0

        embed = default_embed(
            title=f"{member.display_name or member.name}",
            description=f"{member.mention}",
            author=False
        )
        try:
            avatar_url = guild_member.guild_avatar.url if guild_member.guild_avatar else guild_member.avatar.url
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass
        current_rank: NavyRank = get_current_rank(guild_member)

        if current_rank is None:
            embed.add_field(
                name="Current Rank",
                value="No rank found",
            )
            if interaction:
                await interaction.followup.send(embed=embed, ephemeral=True)
            return None, "No rank found"

        current_rank_name = current_rank.name if not is_marine else current_rank.marine_name
        if E2_ROLES[1] in guild_member_role_ids:
            current_rank_name = "Seaman Apprentice"

        embed.add_field(
            name="Current Rank",
            value=f"{current_rank_name}",
        )

        for rank_index in current_rank.promotion_index:
            next_rank = get_rank_by_index(rank_index)

            requirements=""
            additional_requirements=[]
            has_next = False
            match next_rank.index:
                case 2: # Seaman
                    # Check for Seaman Apprentice promotion
                    if E2_ROLES[1] in guild_member_role_ids:
                        latest_apprentice_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, E2_ROLES[1])
                        if not latest_apprentice_role_log:
                            days_with_apprentice = 0
                            requirements += f"\u200b \n **:warning: Please verify role age by hand whilst bot is new**  \n \n"
                        else:
                            days_with_apprentice = get_time_difference_in_days(utc_time_now(), latest_apprentice_role_log.log_time) if latest_apprentice_role_log else None
                        if days_with_apprentice >= 14:
                            requirements += f":x: Has been a Seaman Apprentice for {days_with_apprentice} days (max 14 days) \n"
                        else:
                            requirements += f":information_source: Has been Seaman Apprentice for {days_with_apprentice} days (max 14 days) \n"

                        latest_voyage = voyage_repository.get_last_voyage_by_target_ids([member.id])
                        if latest_voyage:
                            voyage_time = latest_voyage[member.id]
                            days_since_voyage = get_time_difference_in_days(utc_time_now(), voyage_time)
                            if days_since_voyage <= 14:
                                requirements += f":white_check_mark: Had a voyage in the last 14 days ({format_time(get_time_difference(utc_time_now(), voyage_time))} ago) \n"
                            else:
                                requirements += f":x: Had a voyage in the last 14 days ({format_time(get_time_difference(utc_time_now(), voyage_time))} ago) \n"
                    else:
                        ### Prerequisites ###
                        ## Complete 5 total voyages ##
                        if voyage_count >= 5:
                            requirements += f":white_check_mark: Go on five voyages ({voyage_count}/5) \n"
                        else:
                            requirements += f":x: Go on five voyages ({voyage_count}/5) \n"

                        ## Citation of Combat OR Citation of Conduct ##
                        if (has_award_or_higher(guild_member,CITATION_OF_COMBAT,COMBAT_MEDALS)
                        or has_award_or_higher(guild_member,CITATION_OF_CONDUCT,CONDUCT_MEDALS)):
                            requirements += f":white_check_mark: Awarded <@&{CITATION_OF_CONDUCT.role_id}> or <@&{CITATION_OF_COMBAT.role_id}> \n"
                        else:
                            requirements += f":x: Awarded <@&{CITATION_OF_CONDUCT.role_id}> or <@&{CITATION_OF_COMBAT.role_id}> \n"
                case 3: # Able Seaman

                    # if user is seaman apprentice
                    if E2_ROLES[1] in guild_member_role_ids:
                        latest_apprentice_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, E2_ROLES[1])
                        if not latest_apprentice_role_log:
                            days_with_apprentice = 0
                            requirements += f"\u200b \n **:warning: Please verify role age by hand whilst bot is new**  \n \n"
                        else:
                            days_with_apprentice = get_time_difference_in_days(utc_time_now(), latest_apprentice_role_log.log_time) if latest_apprentice_role_log else None
                        if days_with_apprentice >= 14:
                            requirements += f":x: Has been a Seaman Apprentice for {days_with_apprentice} days (max 14 days) \n"
                        else:
                            requirements += f":information_source: Has been Seaman Apprentice for {days_with_apprentice} days (max 14 days) \n"

                        latest_voyage = voyage_repository.get_last_voyage_by_target_ids([member.id])
                        if latest_voyage:
                            voyage_time = latest_voyage[member.id]
                            days_since_voyage = get_time_difference_in_days(utc_time_now(), voyage_time)
                            if days_since_voyage <= 14:
                                requirements += f":white_check_mark: Had a voyage in the last 14 days ({format_time(get_time_difference(utc_time_now(), voyage_time))} ago) \n"
                            else:
                                requirements += f":x: Had a voyage in the last 14 days ({format_time(get_time_difference(utc_time_now(), voyage_time))} ago) \n"
                    else:
                        ### Prerequisites ###
                        ## Complete 5 total voyages ##
                        if voyage_count >= 5:
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
                    latest_e3_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, E3_ROLES[0])
                    if not latest_e3_role_log:
                        requirements += f"\u200b \n **:warning: Please verify role age by hand whilst bot is new**  \n \n"

                    days_with_e3 = get_time_difference_in_days(utc_time_now(), latest_e3_role_log.log_time) if latest_e3_role_log else None
                    if days_with_e3 is None or latest_e3_role_log.change_type != RoleChangeType.ADDED:
                        days_with_e3 = 0

                    # Check the condition for 20 voyages and 7 days first, since it's the higher requirement
                    if voyage_count >= 20:
                        if days_with_e3 >= 7:
                            requirements += f":white_check_mark: Go on twenty voyages ({voyage_count}/20) and wait one week as an E-3 ({days_with_e3}/7) \n"
                        else:
                            requirements += f":x: Go on twenty voyages ({voyage_count}/20) and wait one week as an E-3 ({days_with_e3}/7) \n"
                    # Only if 20 voyages requirement is not in progress or complete, check for 15 voyages and 14 days
                    elif voyage_count >= 15:
                        if days_with_e3 >= 14:
                            requirements += f":white_check_mark: Go on fifteen voyages ({voyage_count}/15) and wait two weeks as an E-3 ({days_with_e3}/14) \n"
                        else:
                            requirements += f":x: Go on fifteen voyages ({voyage_count}/15) and wait two weeks as an E-3 ({days_with_e3}/14) \n"
                    # If neither of the above conditions are met, show both requirements as unmet
                    else:
                        requirements += f":x: Go on fifteen voyages ({voyage_count}/15) and wait two weeks as an E-3 ({days_with_e3}/14) \n"
                        requirements += "**OR**\n"
                        requirements += f":x: Go on twenty voyages ({voyage_count}/20) and wait one week as an E-3 ({days_with_e3}/7) \n"
                        requirements += f"**AND**\n"\

                    ## Completed JLA ##
                    latest_jla_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, JLA_GRADUATE_ROLE)
                    if not latest_jla_role_log:
                        if JLA_GRADUATE_ROLE in netc_guild_member_role_ids:
                            requirements += f":white_check_mark: is a JLA Graduate \n"
                        else:
                            requirements += f":x: is a JLA Graduate \n"
                    elif latest_jla_role_log.change_type == RoleChangeType.ADDED:
                        requirements += f":white_check_mark: is a JLA Graduate \n"
                    else:
                        requirements += f":x: is a JLA Graduate \n"

                    ## Citation of Conduct ##
                    if has_award_or_higher(guild_member,CITATION_OF_CONDUCT,CONDUCT_MEDALS):
                        requirements += f":white_check_mark: Awarded <@&{CITATION_OF_CONDUCT.role_id}> \n"
                    else:
                        requirements += f":x: Awarded <@&{CITATION_OF_CONDUCT.role_id}> \n"

                case 5: #  Petty Officer

                    ### Prerequisites ###
                    ## 10 hosted voyages ##
                    if hosted_count >= 10:
                        requirements += f":white_check_mark: Hosted ten voyages ({hosted_count}/10) \n"
                    else:
                        requirements += f":x: Hosted ten voyages ({hosted_count}/10) \n"
                    ## Have NCO Improvement Ribbon ##
                    if NCO_IMPROVEMENT_RIBBON.role_id in guild_member_role_ids:
                        requirements += f":white_check_mark: Awarded <@&{NCO_IMPROVEMENT_RIBBON.role_id}> \n"
                    else:
                        requirements += f":x: Awarded <@&{NCO_IMPROVEMENT_RIBBON.role_id}> \n"
                    ## Join an SPD ##
                    if any(role in guild_member_role_ids for role in SPD_ROLES):
                        requirements += f":white_check_mark: Joined an SPD \n"
                    else:
                        requirements += f":x: Joined an SPD \n"

                case 6: # Chief Petty Officer

                    ### Prerequisites ###
                    ## 20 hosted voyages ##
                    if hosted_count >= 20:
                        requirements += f":white_check_mark: Hosted twenty voyages ({hosted_count}/20) \n"
                    else:
                        requirements += f":x: Hosted twenty voyages ({hosted_count}/20) \n"

                    latest_snla_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, SNLA_GRADUATE_ROLE)
                    if not latest_snla_role_log:
                        # Given that the bot is new, we can't get the role age
                        if SNLA_GRADUATE_ROLE in netc_guild_member_role_ids:
                            requirements += f":white_check_mark: is a SNLA Graduate \n"
                        else:
                            requirements += f":x: is a SNLA Graduate \n"
                    elif latest_snla_role_log.change_type == RoleChangeType.ADDED:
                        requirements += f":white_check_mark: is a SNLA Graduate \n"
                    else:
                        requirements += f":x: is a SNLA Graduate \n"

                case 8: # Senior Chief Petty Officer

                    ### Prerequisites ###
                    ## 4 month Service Stripe ##
                    if has_award_or_higher(
                        guild_member,
                        FOUR_MONTHS_SERVICE_STRIPES,
                        SERVICE_STRIPES
                    ):
                        requirements += f":white_check_mark: Awarded <@&{FOUR_MONTHS_SERVICE_STRIPES.role_id}> \n"
                    else:
                        requirements += f":x: Awarded <@&{FOUR_MONTHS_SERVICE_STRIPES.role_id}> \n"
                    ## Honorable Conduct Medal ##
                    if has_award_or_higher(guild_member,HONORABLE_CONDUCT,CONDUCT_MEDALS):
                        requirements += f":white_check_mark: Awarded <@&{HONORABLE_CONDUCT.role_id}> \n"
                    else:
                        requirements += f":x: Awarded <@&{HONORABLE_CONDUCT.role_id}> \n"

                    has_next = True

                case 9: # Midshipman

                    ### Prerequisites ###
                    ## 35 hosted voyages ##
                    if hosted_count >= 35:
                        requirements += f":white_check_mark: Hosted thirty-five voyages ({hosted_count}/35) \n"
                    else:
                        requirements += f":x: Hosted thirty-five voyages ({hosted_count}/35) \n"

                    ## Honorable Conduct Medal ##
                    if has_award_or_higher(guild_member,HONORABLE_CONDUCT,CONDUCT_MEDALS):
                        requirements += f":white_check_mark: Awarded <@&{HONORABLE_CONDUCT.role_id}> \n"
                    else:
                        requirements += f":x: Awarded <@&{HONORABLE_CONDUCT.role_id}> \n"

                    ## 4 month Service Stripe ##
                    if has_award_or_higher(
                        guild_member,
                    FOUR_MONTHS_SERVICE_STRIPES,
                        SERVICE_STRIPES
                    ):
                        requirements += f":white_check_mark: Awarded <@&{FOUR_MONTHS_SERVICE_STRIPES.role_id}> \n"
                    else:
                        requirements += f":x: Awarded <@&{FOUR_MONTHS_SERVICE_STRIPES.role_id}> \n"

                    has_next = False

                case 10: # Lieutenant

                    ### Prerequisites ###
                    ## 2 weeks as an O1 ##
                    latest_o1_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id,
                                                                                                    O1_ROLES[0])
                    if not latest_o1_role_log:
                        requirements += f"\u200b \n **:warning: Please verify role age by hand whilst bot is new**  \n \n"

                    days_with_o1 = get_time_difference_in_days(
                        utc_time_now(),
                        latest_o1_role_log.log_time) if latest_o1_role_log else None
                    if days_with_o1 is None or latest_o1_role_log.change_type != RoleChangeType.ADDED:
                        days_with_o1 = 0

                    if days_with_o1 >= 14:
                        requirements += f":white_check_mark: Waited two weeks as an O1 ({days_with_o1}/14) \n"
                    else:
                        requirements += f":x: Waited two weeks as an O1 ({days_with_o1}/14) \n"

                    ## Completed OCS ##
                    latest_ocs_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, OCS_GRADUATE_ROLE)
                    if not latest_ocs_role_log:
                        if OCS_GRADUATE_ROLE in netc_guild_member_role_ids:
                            requirements += f":white_check_mark: is an OCS Graduate \n"
                        else:
                            requirements += f":x: is an OCS Graduate \n"
                    elif latest_ocs_role_log.change_type == RoleChangeType.ADDED:
                        requirements += f":white_check_mark: is an OCS Graduate \n"
                    else:
                        requirements += f":x: is an OCS Graduate \n"

                case 11: # Lieutenant Commander\
                    ### Prerequisites ###
                    ## Completed SOCS ##

                    latest_socs_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, SOCS_GRADUATE_ROLE)
                    if not latest_socs_role_log:
                        if SOCS_GRADUATE_ROLE in netc_guild_member_role_ids:
                            requirements += f":white_check_mark: is an SOCS Graduate \n"
                        else:
                            requirements += f":x: is an SOCS Graduate \n"
                    elif latest_socs_role_log.change_type == RoleChangeType.ADDED:
                        requirements += f":white_check_mark: is an SOCS Graduate \n"
                    else:
                        requirements += f":x: is an SOCS Graduate \n"

                case 12: # Commander

                    ### Prerequisites ###
                    ## 3 to 4 weeks as an O4 ##
                    latest_o4_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, O4_ROLES[0])

                    if not latest_o4_role_log:
                        requirements += f"\u200b \n **:warning: Please verify role age by hand whilst bot is new**  \n \n"

                    days_with_o4 = get_time_difference_in_days(utc_time_now(), latest_o4_role_log.log_time) if latest_o4_role_log else None
                    if days_with_o4 is None or latest_o4_role_log.change_type != RoleChangeType.ADDED:
                        days_with_o4 = 0

                    if days_with_o4 >= 21:
                        requirements += f":white_check_mark: Waited three weeks as an O4 ({days_with_o4}/21) \n"
                    else:
                        requirements += f":x: Waited three weeks as an O4 ({days_with_o4}/21) \n"

                case 13: # Captain

                    ## Prequisites ##
                    ## 2 months as an O5 ##
                    latest_o5_role_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, O5_ROLES[0])

                    if not latest_o5_role_log:
                        requirements += f"\u200b \n **:warning: Please verify role age by hand whilst bot is new**  \n \n"

                    days_with_o5 = get_time_difference_in_days(utc_time_now(), latest_o5_role_log.log_time) if latest_o5_role_log else None
                    if days_with_o5 is None or latest_o5_role_log.change_type != RoleChangeType.ADDED:
                        days_with_o5 = 0

                    if days_with_o5 >= 60:
                        requirements += f":white_check_mark: Waited two months as an O5 ({days_with_o5}/60) \n"
                    else:
                        requirements += f":x: Waited two months as an O5 ({days_with_o5}/60) \n"

                    ## Maritime Service Medal ##
                    if has_award_or_higher(guild_member, MARITIME_SERVICE_MEDAL, HOSTED_MEDALS):
                        requirements += f":white_check_mark: Awarded <@&{MARITIME_SERVICE_MEDAL.role_id}> \n"
                    else:
                        requirements += f":x: Awarded <@&{MARITIME_SERVICE_MEDAL.role_id}> \n"

                case 14:
                    requirements += ":x: Must bribe the Admiral"
                case 16:
                    requirements += ":x: Must bribe the Admiral"
                case 101:
                    requirements += ":x: Viewed [training video #1](https://www.youtube.com/watch?v=dQw4w9WgXcQ)"

            promoting_to: str = next_rank.name if not is_marine else next_rank.marine_name
            # if seaman apprentice
            if E2_ROLES[1] in guild_member_role_ids:
                promoting_to = "Seaman"

            if len(requirements) > 0:
                embed.add_field(
                    name=f"Promotion Requirements - {promoting_to} \n{next_rank.rank_context.embed_url if next_rank.rank_context else ''}",
                    value=f"{requirements}",
                    inline=False
                )

            # If a user has one x
            if requirements.count(":x:") >= 1:
                embed.colour = discord.Colour.red()
            # If an information source is present
            elif requirements.count(":information_source:") >= 1:
                embed.colour = discord.Colour.blue()
            # If no white check marks are present
            elif requirements.count(":white_check_mark:") == 0:
                embed.colour = discord.Colour.blue()
            # If there is more than one white check mark
            elif requirements.count(":white_check_mark:") > 1:
                embed.colour = discord.Colour.green()

            additional_requirements = next_rank.rank_prerequisites.additional_requirements if next_rank.rank_prerequisites else []
            if len(additional_requirements) > 0:
                embed.add_field(
                    name=f"Additional Requirements",
                    value="\n".join(f"- {req}" for req in (additional_requirements if E2_ROLES[1] not in guild_member_role_ids else additional_requirements[1:])),
                    inline=False
                )
            if has_next and E7_ROLES[0] in guild_member_role_ids:
                embed.add_field(
                    name="\u200b",
                    value="**OR** \n \u200b"
                )

        is_eligible = requirements.count(":white_check_mark:") > 0 and requirements.count(":x:") == 0

        if interaction:
            return is_eligible, requirements, embed
        return is_eligible, requirements, embed

    async def check_single_promotion(self, interaction: discord.Interaction, target: discord.Member, ephemeral: bool = False):
        """Handle checking promotion status for a single member."""
        try:
            is_eligible, requirements, embed = await self.check_single_promotion_status(target, interaction)
        except Exception as e:
            await interaction.followup.send(
                f"An error occurred while checking promotion status: {str(e)}", 
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(CheckPromotion(bot))