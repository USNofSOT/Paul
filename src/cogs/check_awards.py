from logging import getLogger

import discord
from discord.ext import commands
from discord import app_commands

from config import GUILD_ID, MEDALS_AND_RIBBONS
from data import Sailor
from data.repository.sailor_repository import SailorRepository
from data.structs import Award

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
                if sailor:
                    role_has_sailors = True
                    msg_str += self.check_sailor(interaction, sailor, member)
                    #msg_str += f"I checked {member.mention}.\n"

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

    def check_sailor(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        # Assert these are the same person
        assert sailor.discord_id == member.id, "Sailor does not have the same ID as discord member."

        msg_str = ""

        # Check voyage medals
        msg_str += self.check_voyages(interaction, sailor, member)
        msg_str += self.check_hosted(interaction, sailor, member)

        return msg_str
    
    def check_voyages(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.voyage_count + sailor.force_voyage_count
        medals = MEDALS_AND_RIBBONS.voyages
        return self._check_awards_by_type(count, medals, interaction, sailor, member)
    
    def check_hosted(self, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
        count = sailor.hosted_count + sailor.force_hosted_count
        medals = MEDALS_AND_RIBBONS.hosted
        return self._check_awards_by_type(count, medals, interaction, sailor, member)
    
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
        msg_str = ""
        msg_str += f"{member.mention} is now eligible for {award_role.mention}.\n"
        msg_str += f"Ranks Responsible: {award.ranks_responsible}\n"
        msg_str += f"Responsible CO: (coming soon)\n"
        msg_str += f"Details: {award.embed_url}\n"
        return msg_str


async def setup(bot: commands.Bot):
    await bot.add_cog(CheckAwards(bot))
