from logging import getLogger

import discord
from discord.ext import commands
from discord import app_commands

from config import GUILD_ID, MEDALS_AND_RIBBONS, SUBCLASS_AWARDS, MAX_MESSAGE_LENGTH
from data import Sailor
from data.repository.sailor_repository import SailorRepository
from data.structs import Award
from utils.report_utils import identify_role_index, process_role_index
from utils.ranks import rank_to_roles

log = getLogger(__name__)


class CheckAwards(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="check_awards", description="Check awards eligibility for a target role")
    @app_commands.describe(role="Mention the role to get a report of")
    async def check_awards(self, interaction: discord.Interaction, role:discord.Role):
        await interaction.response.defer(ephemeral=True)

        # Check if role is defined
        if role is None:
            log.warning("No role mentioned")
            await interaction.followup.send("Please mention a role", ephemeral=True)
            return

        # Get the members of the squad
        members = role.members

        log.info(f"Checking awards for {role.name} with {len(members)} members")

        # Get the repositories
        #self.voyage_repo = VoyageRepository()
        self.sailor_repo = SailorRepository()

        try:
            role_has_sailors = False
            msg_str = ""
            for member in members:
                log.info(f"Checking member {member.name}")
                # Check if member in database
                sailor = self.sailor_repo.get_sailor(member.id)
                if sailor is None:
                    continue
                else:
                    role_has_sailors = True

                # Check for award messages for sailor
                sailor_strs = self.check_sailor(interaction, sailor, member)
                
                # Add strings to message, printing early if message would be too long
                while sailor_strs:
                    sailor_str = sailor_strs.pop(0)
                    if len(msg_str+sailor_str) <= MAX_MESSAGE_LENGTH:
                        msg_str += sailor_str
                    else:
                        await interaction.followup.send(msg_str, ephemeral=True)
                        msg_str = sailor_str

            if not role_has_sailors:
                msg_str = "Role has no sailors in it"
            elif not msg_str:
                msg_str = "All sailors are up-to-date on awards."
            await interaction.followup.send(msg_str, ephemeral=True)

        except Exception as e:
            log.error(f"Error checking awards: {e}")
            await interaction.followup.send("Error checking awards", ephemeral=True)

        finally:
            self.sailor_repo.close_session()

    def check_sailor(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> list[str]:
        # Assert these are the same person
        assert sailor.discord_id == member.id, "Sailor does not have the same ID as discord member."

        msg_strs = [
            # Check awards
            self.check_voyages(interaction, sailor, member),
            self.check_hosted(interaction, sailor, member),
            #FIXME: Add check for combat medals
            #FIXME: Add check for training medals
            #FIXME: Add check for recruiting medals
            #FIXME: Add check for attendance medals
            #FIXME: Add check for service stripes

            # Check subclasses
            self.check_cannoneer(interaction, sailor, member),
            self.check_carpenter(interaction, sailor, member),
            self.check_flex(interaction, sailor, member),
            self.check_helm(interaction, sailor, member),
            self.check_grenadier(interaction, sailor, member),
            self.check_surgeon(interaction, sailor, member),
        ]

        return msg_strs
    
    def check_voyages(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.voyage_count + sailor.force_voyage_count
        medals = MEDALS_AND_RIBBONS.voyages
        return self._check_awards_by_type(count, medals, interaction, sailor, member)
    
    def check_hosted(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.hosted_count + sailor.force_hosted_count
        medals = MEDALS_AND_RIBBONS.hosted
        return self._check_awards_by_type(count, medals, interaction, sailor, member)
    
    # check_combat

    # check_training

    # check_recruiting

    # check_attendance

    # check_service

    def check_cannoneer(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.cannoneer_points + sailor.force_cannoneer_points
        tiers = SUBCLASS_AWARDS.cannoneer
        return self._check_awards_by_type(count, tiers, interaction, sailor, member)

    def check_carpenter(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.carpenter_points + sailor.force_carpenter_points
        tiers = SUBCLASS_AWARDS.carpenter
        return self._check_awards_by_type(count, tiers, interaction, sailor, member)

    def check_flex(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.flex_points + sailor.force_flex_points
        tiers = SUBCLASS_AWARDS.flex
        return self._check_awards_by_type(count, tiers, interaction, sailor, member)

    def check_helm(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.helm_points + sailor.force_helm_points
        tiers = SUBCLASS_AWARDS.helm
        return self._check_awards_by_type(count, tiers, interaction, sailor, member)

    def check_grenadier(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.grenadier_points + sailor.force_grenadier_points
        tiers = SUBCLASS_AWARDS.grenadier
        return self._check_awards_by_type(count, tiers, interaction, sailor, member)

    def check_surgeon(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.surgeon_points + sailor.force_surgeon_points
        tiers = SUBCLASS_AWARDS.surgeon
        return self._check_awards_by_type(count, tiers, interaction, sailor, member)
    
    def _check_awards_by_type(self, count: int, medals: list[Award], interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        msg_str = ""

        # Get award sailor is eligible for
        award = self._find_highest_award(count, medals)
        if award is None:
            return msg_str
        
        # Check if member has award role already
        log.info(f"GUILD_ID: {GUILD_ID}, award role id: {award.role_id}")
        award_role = self.bot.get_guild(GUILD_ID).get_role(award.role_id)
        if award_role not in member.roles:
            msg_str = self._award_message(award, award_role, interaction, member)
        return msg_str
    
    def _find_highest_award(self, count : int, medals : list[Award]) -> None | Award:
        highest = None
        for medal in medals:
            if count >= medal.threshold:
                highest = medal
            else:
                break
        return highest
    
    def _award_message(self, award : Award | None, award_role : discord.Role, interaction: discord.Interaction, member: discord.Member) -> str:
        responsible_co = self._get_responsible_co(interaction, member, award.ranks_responsible)
        
        msg_str = ""
        msg_str += f"{member.mention} is now eligible for {award_role.mention}.\n"
        msg_str += f"\tRanks Responsible: {award.ranks_responsible}\n"
        if responsible_co is not None:
            msg_str += f"\tResponsible CO: {responsible_co.mention}\n"
        msg_str += f"\tDetails: {award.embed_url}\n"
        msg_str += f"\n"
        return msg_str
    
    def _get_responsible_co(self, interaction:discord.Interaction, member: discord.Member, ranks_responsible: str) -> discord.Member | None:
         # Check if NETC/SPD Award
        for spd in ("Logistics","Media","NETC","NRC","NSC","Scheduling"):
           if spd in ranks_responsible:
              return None
    
         # Extract next in command
        role_index = identify_role_index(interaction, member)
        next_in_command = process_role_index(interaction, member, role_index)

        # Return None if process_role_index returns None or str
        if next_in_command is None:
          return None
        if isinstance(next_in_command,str):
            return None
    
        # Guarantee a list and take the last element (current CO)
        if not isinstance(next_in_command,list):
            next_in_command = [next_in_command]
        next_in_command = next_in_command[-1]
        co_member = self.bot.get_guild(GUILD_ID).get_member(next_in_command)

        # Return early for "CO+"
        if ranks_responsible == "CO+":
            return co_member
        
        # Get roles for ranks responsible
        responsible_roles = rank_to_roles(ranks_responsible)

        # Check if CO has any roles
        co_role_ids = [r.id for r in co_member.roles]
        role_intersection = set(responsible_roles).intersection(set(co_role_ids))
        co_has_roles = len(role_intersection) > 0

        # If CO has roles, return them. Otherwise, go up the chain of command
        if co_has_roles:
            responsible_co=co_member
        else:
            responsible_co=self._get_responsible_co(interaction, co_member, ranks_responsible)
        return responsible_co


async def setup(bot: commands.Bot):
    await bot.add_cog(CheckAwards(bot))
