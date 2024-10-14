import discord
from discord.ext import commands
from discord import app_commands
from logging import getLogger
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.data.repository.hosted_repository import HostedRepository

from src.config import NCO_AND_UP

log = getLogger(__name__)


class SquadReport(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="squadreport", description="Get a report of a squad from the last 30 days")
    @app_commands.describe(squad="Mention the squad to get a report of")
    @app_commands.checks.has_any_role(*NCO_AND_UP)
    async def squadreport(self, interaction: discord.Interaction, squad:discord.Role):
        await interaction.response.defer()
        # Check if squad is present in the role
        if squad is None:
            await interaction.response.send_message("Please mention a squad", ephemeral=True)
            return

        if not squad.name.endswith("Squad"):
            await interaction.response.send_message("Please mention a squad", ephemeral=True)
            return

        # Get the members of the squad
        members = squad.members

        # Get the repositories
        voyage_repo = VoyageRepository()
        hosted_repo = HostedRepository()

        try:
            member_voyages = voyage_repo.get_voyages_by_target_id_month_count([member.id for member in members])
            member_hosted = hosted_repo.get_hosted_by_target_ids_month_count([member.id for member in members])

            total_voyage_count = sum([voyage[1] for voyage in member_voyages])
            total_hosted_count = sum([hosted[1] for hosted in member_hosted])

            await interaction.followup.send(f"Total voyages: {total_voyage_count}\nTotal hosted: {total_hosted_count}")
        except Exception as e:
            log.error(f"Error getting squad report: {e}")
            await interaction.followup.send("Error getting squad report", ephemeral=True)
        finally:
            voyage_repo.close_session()
            hosted_repo.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(SquadReport(bot))
