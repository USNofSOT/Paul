from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord import app_commands

from logging import getLogger

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

            embed1 = self.report(squad.name, total_voyage_count, total_hosted_count, members, names_hosted)

            embed2, voyage_graph = self.send_voyage_graph(names_voyage, member_voyages, total_voyage_count)
            embed3, hosted_graph = self.send_hosted_graph(names_hosted, member_hosted, total_hosted_count)
            await interaction.followup.send(embeds=[embed1,embed2,embed3], files=[voyage_graph, hosted_graph],  ephemeral=True)

            os.remove("./voyage_pie_chart.png")
            os.remove("./hosted_pie_chart.png")
        except Exception as e:
            log.error(f"Error getting squad report: {e}")
            await interaction.followup.send("Error getting squad report", ephemeral=True)
        finally:
            voyage_repo.close_session()
            hosted_repo.close_session()

    def send_voyage_graph(self, names: list, member_voyages: list, total_voyage_count: int):
        embed = discord.Embed(title="", color=discord.Color.green())
        # Create a pie chart
        plt.figure(figsize=(10, 8))
        plt.pie(member_voyages, labels=names, autopct=lambda pct: self.avg(pct, total_voyage_count),
                startangle=140, colors=plt.cm.Paired(range(len(names))))

        # Add a title
        plt.title(
            f'Attended voyages from: {(datetime.now() - timedelta(days=30)).date()} to: {datetime.now().date()} - Total: {total_voyage_count}')

        # Save the pie chart to a file
        file_path = "./voyage_pie_chart.png"
        plt.savefig(file_path)
        plt.close()

        # Send the plot image back to the user
        with open(file_path, 'rb') as file:
            discord_file = discord.File(file)
            embed.set_image(url="attachment://voyage_pie_chart.png")

        return embed, discord_file

    def send_hosted_graph(self, names: list, member_hosted: list, total_hosted_count: int):
        embed = discord.Embed(title="", color=discord.Color.green())
        # Create a pie chart
        plt.figure(figsize=(10, 8))
        plt.pie(member_hosted, labels=names, autopct=lambda pct: self.avg(pct, total_hosted_count),
                startangle=140, colors=plt.cm.Paired(range(len(names))))

        # Add a title
        plt.title(
            f'Hosted voyages from: {(datetime.now() - timedelta(days=30)).date()} to: {datetime.now().date()} - Total: {total_hosted_count}')

        # Save the pie chart to a file
        file_path = "./hosted_pie_chart.png"
        plt.savefig(file_path)
        plt.close()

        # Send the plot image back to the user
        with open(file_path, 'rb') as file:
            discord_file = discord.File(file)
            embed.set_image(url="attachment://hosted_pie_chart.png")

        return embed, discord_file

    def report(self, squad_name: str, total_voyage_count: int, total_hosted_count: int, members: list, names_hosted: list):
        embed = discord.Embed(title=f"Squad Report for {squad_name}", color=discord.Color.green())
        embed.add_field(name="Attended voyages", value=f"Total: {total_voyage_count}", inline=True)
        embed.add_field(name="Hosted voyages", value=f"Total: {total_hosted_count}", inline=True)

        embed.add_field(name="Members missing monthly voyage requirement :prohibited:", value="", inline=False)

        no_members = True
        for member in members:
            try:
                memberreport = member_report(member.id)
                if memberreport is None:
                    embed.add_field(name="", value=f"{member.display_name} - Last voyage: N/A", inline=False)
                    no_members = False
                    continue
                if get_time_difference_past(memberreport.last_voyage).days >= 30:
                    embed.add_field(name="", value=f"{member.display_name} - Last voyage: {format_time(get_time_difference_past(memberreport.last_voyage))}", inline=False)
                    no_members = False
            except Exception as e:
                log.error(f"Error getting member report: {e}")

        if no_members:
            embed.add_field(name="", value="All members have voyaged :white_check_mark:", inline=False)

        embed.add_field(name="Members missing biweekly hosting requirement :prohibited:", value="", inline=False)

        no_members = True
        for member in members:
            try:
                memberreport = member_report(member.id)
                if member.display_name in names_hosted:
                    if get_time_difference_past(memberreport.last_hosted).days >= 14:
                        embed.add_field(name="", value=f"{member.display_name} - Last hosted: {format_time(get_time_difference_past(memberreport.last_hosted))}", inline=False)
                        no_members = False
            except Exception as e:
                log.error(f"Error getting member report: {e}")

        if no_members:
            embed.add_field(name="", value="All members have hosted :white_check_mark:", inline=False)

        return embed

    def avg(self, pct, total):
        absolute = round(pct / 100. * total)
        return f'{absolute} ({pct:.1f}%)'


async def setup(bot: commands.Bot):
    await bot.add_cog(SquadReport(bot))
