from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord import app_commands

from logging import getLogger

from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.data.repository.hosted_repository import HostedRepository
from src.config import NCO_AND_UP
from src.data import MemberReport, member_report
from src.utils.time_utils import get_time_difference_past, format_time

import os

import matplotlib.pyplot as plt

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
            member_voyages_dict = voyage_repo.get_voyages_by_target_id_month_count([member.id for member in members])
            member_hosted_dict = hosted_repo.get_hosted_by_target_ids_month_count([member.id for member in members])

            names_voyage = [member.display_name for id in member_voyages_dict.keys() for member in members if member.id == id]
            names_hosted = [member.display_name for id in member_hosted_dict.keys() for member in members if member.id == id]

            member_voyages = [member_voyages_dict[id] for id in member_voyages_dict.keys()]
            member_hosted = [member_hosted_dict[id] for id in member_hosted_dict.keys()]

            total_voyage_count = sum([voyage for voyage in member_voyages])
            total_hosted_count = sum([hosted for hosted in member_hosted])

            await self.send_embed(squad.name, interaction, total_voyage_count, total_hosted_count, members, names_hosted)

            await self.send_voyage_graph(interaction, names_voyage, member_voyages, total_voyage_count)
            await self.send_hosted_graph(interaction, names_hosted, member_hosted, total_hosted_count)


        except Exception as e:
            log.error(f"Error getting squad report: {e}")
            await interaction.followup.send("Error getting squad report", ephemeral=True)
        finally:
            voyage_repo.close_session()
            hosted_repo.close_session()

    async def send_voyage_graph(self, interaction: discord.Interaction, names: list, member_voyages: list, total_voyage_count: int):
        # Create a pie chart
        plt.figure(figsize=(10, 8))
        plt.pie(member_voyages, labels=names, autopct=lambda pct: self.avg(pct, total_voyage_count),
                startangle=140, colors=plt.cm.Paired(range(len(names))))

        # Add a title
        plt.title(
            f'Attended voyages from: {(datetime.now() - timedelta(days=30)).date()} to: {datetime.now().date()} - Total: {total_voyage_count}')

        # Save the pie chart to a file
        file_path = "./squadreport_pie_chart.png"
        plt.savefig(file_path)
        plt.close()

        # Send the plot image back to the user
        with open(file_path, 'rb') as file:
            await interaction.followup.send(file=discord.File(file, filename="squadreport_pie_chart.png"),
                                            ephemeral=True)

        # Delete the file
        os.remove(file_path)

    async def send_hosted_graph(self, interaction: discord.Interaction, names: list, member_hosted: list, total_hosted_count: int):
        # Create a pie chart
        plt.figure(figsize=(10, 8))
        plt.pie(member_hosted, labels=names, autopct=lambda pct: self.avg(pct, total_hosted_count),
                startangle=140, colors=plt.cm.Paired(range(len(names))))

        # Add a title
        plt.title(
            f'Hosted voyages from: {(datetime.now() - timedelta(days=30)).date()} to: {datetime.now().date()} - Total: {total_hosted_count}')

        # Save the pie chart to a file
        file_path = "./squadreport_pie_chart.png"
        plt.savefig(file_path)
        plt.close()

        # Send the plot image back to the user
        with open(file_path, 'rb') as file:
            await interaction.followup.send(file=discord.File(file, filename="squadreport_pie_chart.png"),
                                            ephemeral=True)

        # Delete the file
        os.remove(file_path)

    async def send_embed(self, squad_name: str, interaction: discord.Interaction, total_voyage_count: int, total_hosted_count: int, members: list, names_hosted: list):
        embed = discord.Embed(title=f"Squad Report for {squad_name}", color=discord.Color.green())
        embed.add_field(name="Attended voyages", value=f"Total: {total_voyage_count}", inline=True)
        embed.add_field(name="Hosted voyages", value=f"Total: {total_hosted_count}", inline=True)

        embed.add_field(name="Members missing monthly voyage requirement :prohibited:", value="None", inline=False)
        for member in members:
            memberreport = member_report(member.id)

            if memberreport.last_voyage is None:
                embed.add_field(name=f"{member.display_name}", value="Last voyage: N/A", inline=True)
            if get_time_difference_past(memberreport.last_voyage).days >= 30:
                embed.add_field(name=f"{member.display_name}", value=f"Last voyage: {format_time(get_time_difference_past(memberreport.last_voyage))}", inline=True)

        embed.add_field(name="Members missing biweekly hosting requirement :prohibited:", value="None", inline=False)
        for member in members:
            memberreport = member_report(member.id)
            if member.display_name in names_hosted:
                if get_time_difference_past(memberreport.last_hosted).days >= 30:
                    embed.add_field(name=f"{member.display_name}", value=f"Last hosted: {format_time(get_time_difference_past(memberreport.last_hosted))}", inline=True)


        await interaction.followup.send(embed=embed, ephemeral=True)

    def avg(self, pct, total):
        absolute = round(pct / 100. * total)
        return f'{absolute} ({pct:.1f}%)'


async def setup(bot: commands.Bot):
    await bot.add_cog(SquadReport(bot))
