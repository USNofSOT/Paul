import os
from datetime import datetime, timedelta
from logging import getLogger

import discord
import matplotlib.pyplot as plt
from discord import app_commands
from discord.ext import commands

from src.config import NCO_AND_UP, NCO_AND_UP_PURE, NSC_ROLES
from src.config.ranks_roles import BOA_ROLE
from src.config.requirements import (
    HOSTING_REQUIREMENT_IN_DAYS,
    VOYAGING_REQUIREMENT_IN_DAYS,
)
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.utils.discord_utils import get_best_display_name
from src.utils.time_utils import get_time_difference_past

log = getLogger(__name__)


class CrewReport(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="crewreport", description="Get a report of a squad or a ship from the last 30 days")
    @app_commands.describe(crew="Mention the squad or ship to get a report of")
    @app_commands.checks.has_any_role(*NCO_AND_UP)
    async def crewreport(self, interaction: discord.Interaction, crew:discord.Role):
        await interaction.response.defer(ephemeral=True)
        # Check if squad is present in the role
        if crew is None:
            log.warning("No squad or ship mentioned")
            await interaction.followup.send("Please mention a squad or a ship", ephemeral=True)
            return

        member_role_ids = [role.id for role in interaction.user.roles]
        if not crew.name.endswith("Squad") and not crew.name.startswith("USS"):
            if any(role in member_role_ids for role in [BOA_ROLE, *NSC_ROLES]):
                pass
            else:
                log.warning("Invalid squad or ship mentioned")
                await interaction.followup.send("Please mention a squad or a ship", ephemeral=True)
                return

        # Get the members of the squad
        members = crew.members

        log.info(f"Generating crew report for {crew.name} with {len(members)} members")

        # Get the repositories
        self.voyage_repo = VoyageRepository()
        self.hosted_repo = HostedRepository()

        try:
            member_voyages_dict = self.voyage_repo.get_voyages_by_target_id_month_count([member.id for member in members])
            member_hosted_dict = self.hosted_repo.get_hosted_by_target_ids_month_count([member.id for member in members])

            member_voyages_dict = dict(sorted(member_voyages_dict.items(), key=lambda item: item[1], reverse=True))
            member_hosted_dict = dict(sorted(member_hosted_dict.items(), key=lambda item: item[1], reverse=True))

            names_voyage = [member.display_name for id in member_voyages_dict.keys() for member in members if member.id == id]
            names_hosted = [member.display_name for id in member_hosted_dict.keys() for member in members if member.id == id]

            member_voyages = [member_voyages_dict[id] for id in member_voyages_dict.keys()]
            member_hosted = [member_hosted_dict[id] for id in member_hosted_dict.keys()]

            total_voyage_count = sum(member_voyages)
            total_hosted_count = sum(member_hosted)

            embed1 = await self.report(crew.name, total_voyage_count, total_hosted_count, members, names_hosted, interaction)

            embed2, voyage_graph = self.send_voyage_graph(names_voyage, member_voyages, total_voyage_count)
            embed3, hosted_graph = self.send_hosted_graph(names_hosted, member_hosted, total_hosted_count)
            await interaction.followup.send(embeds=[embed1,embed2,embed3], files=[voyage_graph, hosted_graph], ephemeral=True)


        except Exception as e:
            log.error(f"Error getting squad report: {e}", exc_info=True)
            await interaction.followup.send("Error getting squad report", ephemeral=True)
        finally:
            self.voyage_repo.close_session()
            self.hosted_repo.close_session()
        try:
            os.remove("./voyage_pie_chart.png")
            os.remove("./hosted_pie_chart.png")
        except Exception as e:
            log.error(f"Error removing file: {e}")

    def send_voyage_graph(self, names: list, member_voyages: list, total_voyage_count: int):
        embed = discord.Embed(title="", color=discord.Color.green())

        colors = plt.cm.tab20(range(len(names)))

        # Create a bar graph
        plt.figure(figsize=(15, 12))
        max_value = max(member_voyages)
        plt.ylim(0, max_value + 2)
        plt.bar(names, member_voyages, color=colors)
        plt.xticks(rotation=45, ha='right')
        for i, v in enumerate(member_voyages):
            plt.text(i, v + 0.5, str(v), color='black', ha='center')


        # Add a title
        plt.title(
            f'Attended voyages from: {(datetime.now() - timedelta(days=30)).date()} to: {datetime.now().date()} - Total: {total_voyage_count}')

        plt.margins(0.05)
        plt.tight_layout()

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

        colors = plt.cm.tab20(range(len(names)))

        # Create a bar graph
        plt.figure(figsize=(15, 12))
        max_value = max(member_hosted)
        plt.ylim(0, max_value + 2)
        plt.bar(names, member_hosted, color=colors)
        plt.xticks(rotation=45, ha='right')
        for i, v in enumerate(member_hosted):
            plt.text(i, v + 0.1, str(v), color='black', ha='center')

        # Add a title
        plt.title(
            f'Hosted voyages from: {(datetime.now() - timedelta(days=30)).date()} to: {datetime.now().date()} - Total: {total_hosted_count}')

        plt.margins(0.05)
        plt.tight_layout()

        # Save the pie chart to a file
        file_path = "./hosted_pie_chart.png"
        plt.savefig(file_path)
        plt.close()

        # Send the plot image back to the user
        with open(file_path, 'rb') as file:
            discord_file = discord.File(file)
            embed.set_image(url="attachment://hosted_pie_chart.png")

        return embed, discord_file

    async def report(self, crew_name: str, total_voyage_count: int, total_hosted_count: int, members: list, names_hosted: list, interaction: discord.Interaction):
        embed = discord.Embed(title=f"Crew Report for {crew_name}", color=discord.Color.green())
        embed.add_field(name="Attended voyages", value=f"Total: {total_voyage_count}", inline=True)
        embed.add_field(name="Hosted voyages", value=f"Total: {total_hosted_count}", inline=True)

        embed.add_field(name="Members missing monthly voyage requirement :prohibited:", value="", inline=False)

        last_voyages = self.voyage_repo.get_last_voyage_by_target_ids([member.id for member in members])

        no_members = True
        voyager_dictionary = {}

        for member in members:
            if last_voyages.get(member.id) is None:
                voyager_dictionary[member.id] = "N/A"
                no_members = False
            elif get_time_difference_past(last_voyages.get(member.id)).days >= VOYAGING_REQUIREMENT_IN_DAYS:
                voyager_dictionary[member.id] = get_time_difference_past(last_voyages.get(member.id))
                no_members = False

        if len(voyager_dictionary) > 15:
            embed.add_field(name="", value="Too many members to display, see csv file", inline=False)
            with open("voyager_report.csv", "w") as file:
                file.write("Member,Last Voyage\n")
                for voyager in voyager_dictionary:
                    file.write(f"{get_best_display_name(self.bot, voyager)},{voyager_dictionary[voyager]}\n")
            await interaction.followup.send(file=discord.File("voyager_report.csv"), content="CSV file with all members that have not voyaged in the last 30 days")
        else:
            for voyager in voyager_dictionary:
                embed.add_field(name="", value=f"{get_best_display_name(self.bot, voyager)} - Last voyage: {voyager_dictionary[voyager]}", inline=False)


        if no_members:
            embed.add_field(name="", value="All members have voyaged :white_check_mark:", inline=False)

        embed.add_field(name="Members missing biweekly hosting requirement :prohibited:", value="", inline=False)

        last_hosted = self.hosted_repo.get_last_hosted_by_target_ids([member.id for member in members])
        no_members = True

        hoster_dictionary = {}

        for member in members:
            member_roles = [role for role in member.roles]
            member_role_ids = [role.id for role in member_roles]
            if any(role in member_role_ids for role in NCO_AND_UP_PURE):
                if last_hosted.get(member.id) is None:
                    ship_name = [role.name for role in member_roles if role.name.startswith("USS")]
                    hoster_dictionary[member.id] = {
                        "last_hosted": "N/A",
                        "ship": ship_name[0] if ship_name else "N/A"
                    }
                    no_members = False
                elif get_time_difference_past(last_hosted.get(member.id)).days >= HOSTING_REQUIREMENT_IN_DAYS:
                    ship_name = [role.name for role in member_roles if role.name.startswith("USS")]
                    hoster_dictionary[member.id] = {
                        "last_hosted": get_time_difference_past(last_hosted.get(member.id)),
                        "ship": ship_name[0] if ship_name else "N/A"
                    }
                    no_members = False

        if len(hoster_dictionary) > 24:
            embed.add_field(name="", value="Too many members to display, see csv file", inline=False)
            with open("hoster_report.csv", "w") as file:
                file.write("Member,Last Hosted,Ship\n")
                for hoster in hoster_dictionary:
                    file.write(f"{get_best_display_name(self.bot, hoster)},{hoster_dictionary[hoster]['last_hosted']},{hoster_dictionary[hoster]['ship']}\n")
                await interaction.followup.send(file=discord.File("crew_report.csv"), content="CSV file with all members that have not hosted in the last 21 days")
        else:
            for hoster in hoster_dictionary:
                embed.add_field(name="", value=f"{get_best_display_name(self.bot, hoster)} - Last hosted: {hoster_dictionary[hoster]['last_hosted']} on {hoster_dictionary[hoster]['ship']}", inline=False)

        if no_members:
            embed.add_field(name="", value="All members have hosted :white_check_mark:", inline=False)

        return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(CrewReport(bot))
