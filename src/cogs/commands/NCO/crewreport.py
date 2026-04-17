from datetime import datetime, timedelta
from logging import getLogger

import discord
import matplotlib.pyplot as plt
from discord import app_commands
from discord.ext import commands

from src.config import IMAGE_CACHES
from src.config.requirements import (
    HOSTING_REQUIREMENT_IN_DAYS,
    VOYAGING_REQUIREMENT_IN_DAYS,
)
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.security import require_any_role, Role, resolve_effective_roles
from src.utils.discord_utils import get_best_display_name
from src.utils.image_cache import BinaryImageCache, render_matplotlib_plot_to_png
from src.utils.time_utils import get_time_difference_past

log = getLogger(__name__)

CREWREPORT_VOYAGE_CACHE = BinaryImageCache(IMAGE_CACHES["crewreport_voyage_chart"])
CREWREPORT_HOSTED_CACHE = BinaryImageCache(IMAGE_CACHES["crewreport_hosted_chart"])


def render_empty_bar_chart(message: str, title: str) -> bytes:
    def plotter():
        plt.figure(figsize=(15, 12))
        plt.title(title)
        plt.text(0.5, 0.5, message, ha="center", va="center", fontsize=16)
        plt.axis("off")
        plt.tight_layout()

    return render_matplotlib_plot_to_png(plotter)


class CrewReport(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="crewreport", description="Get a report of a squad or a ship from the last 30 days")
    @app_commands.describe(crew="Mention the squad or ship to get a report of")
    @require_any_role(Role.NCO)
    async def crewreport(self, interaction: discord.Interaction, crew:discord.Role):
        await interaction.response.defer(ephemeral=True)
        # Check if squad is present in the role
        if crew is None:
            log.warning("No squad or ship mentioned")
            await interaction.followup.send("Please mention a squad or a ship", ephemeral=True)
            return

        user_roles = resolve_effective_roles(interaction.user)
        if not crew.name.endswith("Squad") and not crew.name.startswith("USS"):
            if Role.BOA in user_roles or Role.NSC_OBSERVER in user_roles:
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

    def send_voyage_graph(self, names: list, member_voyages: list, total_voyage_count: int):
        embed = discord.Embed(title="", color=discord.Color.green())
        now = datetime.now()
        start_date = (now - timedelta(days=30)).date().isoformat()
        end_date = now.date().isoformat()
        cache_payload = {
            "names": names,
            "member_voyages": member_voyages,
            "total_voyage_count": total_voyage_count,
            "start_date": start_date,
            "end_date": end_date,
        }

        if not names or not member_voyages:
            image_data = CREWREPORT_VOYAGE_CACHE.get_or_create_bytes(
                {**cache_payload, "empty": True},
                lambda: render_empty_bar_chart(
                    "No voyage activity found for this period.",
                    f"Attended voyages from: {start_date} to: {end_date}",
                ),
            )
            discord_file = CREWREPORT_VOYAGE_CACHE.to_discord_file(image_data)
            embed.set_image(
                url=f"attachment://{CREWREPORT_VOYAGE_CACHE.config.default_filename}"
            )
            return embed, discord_file

        def plotter():
            colors = plt.cm.tab20(range(len(names)))
            plt.figure(figsize=(15, 12))
            max_value = max(member_voyages)
            plt.ylim(0, max_value + 2)
            plt.bar(names, member_voyages, color=colors)
            plt.xticks(rotation=45, ha='right')
            for index, value in enumerate(member_voyages):
                plt.text(index, value + 0.5, str(value), color='black', ha='center')

            plt.title(
                f"Attended voyages from: {start_date} to: {end_date} - Total: {total_voyage_count}"
            )
            plt.margins(0.05)
            plt.tight_layout()

        image_data = CREWREPORT_VOYAGE_CACHE.get_or_create_bytes(
            cache_payload,
            lambda: render_matplotlib_plot_to_png(plotter),
        )
        discord_file = CREWREPORT_VOYAGE_CACHE.to_discord_file(image_data)
        embed.set_image(
            url=f"attachment://{CREWREPORT_VOYAGE_CACHE.config.default_filename}"
        )
        return embed, discord_file

    def send_hosted_graph(self, names: list, member_hosted: list, total_hosted_count: int):
        embed = discord.Embed(title="", color=discord.Color.green())
        now = datetime.now()
        start_date = (now - timedelta(days=30)).date().isoformat()
        end_date = now.date().isoformat()
        cache_payload = {
            "names": names,
            "member_hosted": member_hosted,
            "total_hosted_count": total_hosted_count,
            "start_date": start_date,
            "end_date": end_date,
        }

        if not names or not member_hosted:
            image_data = CREWREPORT_HOSTED_CACHE.get_or_create_bytes(
                {**cache_payload, "empty": True},
                lambda: render_empty_bar_chart(
                    "No hosted activity found for this period.",
                    f"Hosted voyages from: {start_date} to: {end_date}",
                ),
            )
            discord_file = CREWREPORT_HOSTED_CACHE.to_discord_file(image_data)
            embed.set_image(
                url=f"attachment://{CREWREPORT_HOSTED_CACHE.config.default_filename}"
            )
            return embed, discord_file

        def plotter():
            colors = plt.cm.tab20(range(len(names)))
            plt.figure(figsize=(15, 12))
            max_value = max(member_hosted)
            plt.ylim(0, max_value + 2)
            plt.bar(names, member_hosted, color=colors)
            plt.xticks(rotation=45, ha='right')
            for index, value in enumerate(member_hosted):
                plt.text(index, value + 0.1, str(value), color='black', ha='center')

            plt.title(
                f"Hosted voyages from: {start_date} to: {end_date} - Total: {total_hosted_count}"
            )
            plt.margins(0.05)
            plt.tight_layout()

        image_data = CREWREPORT_HOSTED_CACHE.get_or_create_bytes(
            cache_payload,
            lambda: render_matplotlib_plot_to_png(plotter),
        )
        discord_file = CREWREPORT_HOSTED_CACHE.to_discord_file(image_data)
        embed.set_image(
            url=f"attachment://{CREWREPORT_HOSTED_CACHE.config.default_filename}"
        )
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
