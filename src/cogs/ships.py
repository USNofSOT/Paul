from datetime import datetime, timedelta
from logging import getLogger

import discord
from dateutil.relativedelta import relativedelta
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from matplotlib import pyplot as plt

from src.config import NSC_ROLES
from src.config.main_server import GUILD_ID
from src.config.ranks_roles import SNCO_AND_UP, E8_AND_UP, E6_AND_UP, BOA_ROLE
from src.config.ships import SHIPS
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.utils.embeds import error_embed

log = getLogger(__name__)


class Ships(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.hosted_repository = None
        self.voyage_repository = None
        self.top_voyagers = {}
        self.top_hosts = {}
        self.top_voyage_ships = {}
        self.top_hosts_ships = {}
        self.ships = {}
        self.selected_ships = set()
        self.total_voyages = 0
        self.total_hosted = 0

    @app_commands.command(name="ships", description="Get a report of ship activity")
    @app_commands.describe(ship="Optionally provide a ship to get more detailed information about")
    @app_commands.describe(hidden="Should only you be able to see the response?")
    @app_commands.choices(
        only=[
            Choice(name="Performers", value="performers"),
            Choice(name="Ships", value="ships"),
            Choice(name="Drilldown", value="drilldown"),
            Choice(name="Trends", value="trends")
        ]
    )
    @app_commands.describe(only="Optionally provide a specific report to get")
    @app_commands.checks.has_any_role(BOA_ROLE, *NSC_ROLES)
    @app_commands.checks.cooldown(1, 30)
    async def ships(self, interaction: discord.Interaction, ship: discord.Role = None, hidden: bool = True, only: str = None):
        self.top_voyagers = {}
        self.top_hosts = {}
        self.top_voyage_ships = {}
        self.top_hosts_ships = {}
        self.ships = {}
        self.selected_ships = set()
        self.total_voyages = 0
        self.total_hosted = 0

        try:
            await interaction.response.defer(ephemeral=hidden)

            self.hosted_repository = HostedRepository()
            self.voyage_repository = VoyageRepository()

            # 1. Load in all information
            roles = []
            for role_id in [s.role_id for s in SHIPS]:
                roles.append(discord.utils.get(interaction.guild.roles, id=role_id))
            for role in roles:
                self.get_info(role)

            if ship and ship.id not in [s.role_id for s in SHIPS]:
                for member in ship.members:
                    for role in member.roles:
                        if role.id in [s.role_id for s in SHIPS]:
                            self.selected_ships.add(role.id)
            elif ship and ship.id in [s.role_id for s in SHIPS]:
                self.selected_ships.add(ship.id)
            if self.selected_ships:
                self.ships = {ship: self.ships[ship] for ship in self.selected_ships}

            if only == "performers":
                performers_embed = self.get_performers_embed()
                await interaction.followup.send(embed=performers_embed)
                return
            elif only == "ships":
                ships_embed = self.get_ships_embed()
                await interaction.followup.send(embed=ships_embed)
                return
            elif only == "drilldown":
                if not ship:
                    await interaction.followup.send(embed=error_embed("No ship provided"), ephemeral=True)
                    return
                ship_embed = self.get_ship_embed(ship.id)
                await interaction.followup.send(embed=ship_embed)
                return
            elif only == "trends":
                trend_voyages_embed, trend_voyages_file = await self.trend_voyages_past_months(interaction)
                trend_hosted_embed, trend_hosted_file = await self.trend_hosted_past_month(interaction)
                await interaction.followup.send(embeds=[trend_voyages_embed, trend_hosted_embed], files=[trend_voyages_file, trend_hosted_file])
                return

            # 2. Get the embed for displaying the best performers
            performers_embed = self.get_performers_embed()

            # 3. Get the embed for displaying the ship statistics
            ships_embed = self.get_ships_embed()

            # 3.2 Get the embed for displaying the ship trends
            trend_voyages_embed, trend_voyages_file = await self.trend_voyages_past_months(interaction)
            trend_hosted_embed, trend_hosted_file = await self.trend_hosted_past_month(interaction)

            # 4. Check if a ship was provided
            ship_embed = None
            if ship and ship.id in [s.role_id for s in SHIPS]:
                ship_embed = self.get_ship_embed(ship.id)

            if ship_embed:
                await interaction.followup.send(embeds=[performers_embed, ships_embed, ship_embed, trend_voyages_embed, trend_hosted_embed], files=[trend_voyages_file, trend_hosted_file])
            else:
                await interaction.followup.send(embeds=[performers_embed, ships_embed, trend_voyages_embed, trend_hosted_embed], files=[trend_voyages_file, trend_hosted_file])
        except Exception as e:
            log.error(f"Error getting ships: {e}", exc_info=True)
            await interaction.followup.send(embed=error_embed("Error getting ships"), ephemeral=True)
        finally:
            self.hosted_repository.close_session()
            self.voyage_repository.close_session()

    def get_performers_embed(self):
        embed = discord.Embed(
            title="Navy Wide Ship Performers Report",
            color=discord.Color.yellow(),
            description=f"Report for ship activity from **{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}** to **{datetime.now().strftime('%Y-%m-%d')}**"
        )

        embed.add_field(name="Total Hosted", value=self.total_hosted, inline=True)
        embed.add_field(name="Total Voyages", value=self.total_voyages, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        top_hosts = {}
        for member_id, hosted in list(self.top_hosts.items())[:5]:
            member = discord.utils.get(self.bot.get_guild(GUILD_ID).members, id=member_id)
            top_hosts[member_id] = hosted
        embed.add_field(name=":trophy: Top 5 Hosts", value="\n".join([f"{index + 1}. <@{member_id}>: \n {hosted} ({round(hosted/self.total_voyages * 100, 1) if self.total_voyages > 0 else 0}%)" for index, (member_id, hosted) in enumerate(top_hosts.items())]), inline=True)
        top_voyagers = {}
        for member_id, voyages in list(self.top_voyagers.items())[:5]:
            member = discord.utils.get(self.bot.get_guild(GUILD_ID).members, id=member_id)
            top_voyagers[member_id] = voyages
        embed.add_field(name=":trophy: Top 5 Voyagers", value="\n".join([f"{index + 1}. <@{member_id}>: \n {voyages} ({round(voyages/self.total_voyages * 100, 1) if self.total_voyages > 0 else 0}%)" for index, (member_id, voyages) in enumerate(top_voyagers.items())]), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

        top_hosting = {}
        for ship, hosted in list(self.top_hosts_ships.items())[:5]:
            top_hosting[ship] = hosted
        embed.add_field(name=":ship: Top 5 Hosting Ships", value="\n".join([f"{index + 1}. <@&{ship}>: \n {hosted} ({round(hosted / self.total_voyages * 100, 1) if self.total_voyages > 0 else 0}%)" for index, (ship, hosted) in enumerate(top_hosting.items())]), inline=True)
        top_voyages = {}
        for ship, voyages in list(self.top_voyage_ships.items())[:5]:
            top_voyages[ship] = voyages
        embed.add_field(name=":ship: Top 5 Voyaging Ships", value="\n".join([f"{index + 1}. <@&{ship}>: \n {voyages} ({round(voyages / self.total_voyages * 100, 1) if self.total_voyages > 0 else 0}%)" for index, (ship, voyages) in enumerate(top_voyages.items())]), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

        return embed


    def get_ships_embed(self):
        embed = discord.Embed(
            title="Ship Statistics Report",
            color=discord.Color.blue(),
            description=f"Report for ship activity from **{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}** to **{datetime.now().strftime('%Y-%m-%d')}**"
        )

        for ship, stats in sorted(self.ships.items(), key=lambda item: item[1]['Voyages'] + item[1]['Hosted'], reverse=True):
            ship_emoji = self.get_ship_by_role_id(ship).emoji or ":ship:"
            role_name = self.bot.get_guild(GUILD_ID).get_role(int(ship)).name
            embed.add_field(name=f"{ship_emoji} {role_name}", value=f"Total Members: {stats['Total Members']}\nTotal Hosts: {stats['Total Hosts']}\nVoyages: {stats['Voyages']}\nHosted: {stats['Hosted']}", inline=True)
        return embed

    def get_ship_embed(self, ship):
        ship_role = self.bot.get_guild(GUILD_ID).get_role(int(ship))
        ship = self.ships[ship]
        embed = discord.Embed(
            title=f"Ship Drilldown Report for {ship_role.name}",
            color=discord.Color.green(),
            description=f"Report for ship activity from **{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}** to **{datetime.now().strftime('%Y-%m-%d')}**"
        )

        ship_members = [member for member in self.bot.get_guild(GUILD_ID).members if ship_role in member.roles]

        total_hosted_in_ship = len(self.hosted_repository.get_hosted_by_role_ids_and_between_dates([ship_role.id], datetime.now() - timedelta(days=30), datetime.now()))
        embed.add_field(name="Total Hosted", value=total_hosted_in_ship, inline=True)
        embed.add_field(name="Total Voyages", value=ship['Voyages'], inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

        top_hosts = {}
        for member_id, hosted in list(self.top_hosts.items()):
            if member_id in [member.id for member in ship_members]:
                top_hosts[member_id] = len(
                    self.hosted_repository.get_hosted_by_role_ids_and_target_ids_and_between_dates(
                        [ship_role.id],
                        [member_id],
                        datetime.now() - timedelta(days=30),
                        datetime.now()
                    )
                )
        embed.add_field(name=":trophy: Top Ship Hosts", value="\n".join([f"- <@{member_id}>: \n Monthly rank: **#{list(self.top_hosts.keys()).index(member_id) + 1}** \n Total hosted: **{hosted}** \n Percentage Hosted (Ship): **{round(hosted/total_hosted_in_ship * 100, 1) if total_hosted_in_ship > 0 else 0}%** \n Percentage Hosted (Navy): **{round(hosted/self.total_voyages * 100, 1) if self.total_voyages > 0 else 0}%**" for member_id, hosted in top_hosts.items()][:5]), inline=True)
        top_voyagers = {}
        for member_id, voyages in list(self.top_voyagers.items()):
            if member_id in [member.id for member in ship_members]:
                top_voyagers[member_id] = len(
                    self.voyage_repository.get_voyages_by_role_ids_and_target_ids_and_between_dates(
                        [ship_role.id],
                        [member_id],
                        datetime.now() - timedelta(days=30),
                        datetime.now()
                    )
                )
        embed.add_field(name=":trophy: Top Ship Voyagers", value="\n".join([f"- <@{member_id}>: \n Monthly rank: **#{list(self.top_voyagers.keys()).index(member_id) + 1}**  \n Total voyages: **{voyages}** \n Percentage Voyages (Ship): **{round(voyages/ship['Voyages'] * 100, 1) if ship['Voyages'] > 0 else 0}%** \n Percentage Voyages (Navy): **{round(voyages/self.total_voyages * 100, 1) if self.total_voyages > 0 else 0}%**" for member_id, voyages in top_voyagers.items()][:5]), inline=True)

        return embed


    def get_info(self, role: discord.Role) -> None:
        host_ids = []
        member_ids = []

        for member in role.members:
            if any(role.name in ["Voyage Permissions"] for role in member.roles):
                host_ids.append(member.id)
            member_ids.append(member.id)

        hosted = self.hosted_repository.get_hosted_by_target_ids_month_count(host_ids)
        hosted_count = len(self.hosted_repository.get_hosted_by_role_ids_and_between_dates([role.id], datetime.now() - timedelta(days=30), datetime.now()))


        voyages = self.voyage_repository.get_voyages_by_target_id_month_count(member_ids)
        voyages_count = len(self.voyage_repository.get_voyages_by_role_ids_and_between_dates([role.id], datetime.now() - timedelta(days=30), datetime.now()))

        for member_id in member_ids:
            if member_id in voyages:
                self.top_voyagers[member_id] = len(
                    self.voyage_repository.get_voyages_by_role_ids_and_target_ids_and_between_dates(
                        [role.id],
                        [member_id],
                        datetime.now() - timedelta(days=30),
                        datetime.now()
                    )
                )

        self.top_voyagers = dict(sorted(self.top_voyagers.items(), key=lambda item: item[1], reverse=True))

        for host_id in host_ids:
            if host_id in hosted:
                self.top_hosts[host_id] = len(
                    self.hosted_repository.get_hosted_by_role_ids_and_target_ids_and_between_dates(
                        [role.id],
                        [host_id],
                        datetime.now() - timedelta(days=30),
                        datetime.now()
                    )
                )

        self.top_hosts = dict(sorted(self.top_hosts.items(), key=lambda item: item[1], reverse=True))

        self.top_voyage_ships[role.id] = voyages_count
        self.top_hosts_ships[role.id] = hosted_count
        self.top_voyage_ships = dict(sorted(self.top_voyage_ships.items(), key=lambda item: item[1], reverse=True))
        self.top_hosts_ships = dict(sorted(self.top_hosts_ships.items(), key=lambda item: item[1], reverse=True))

        self.total_hosted += hosted_count
        self.total_voyages += voyages_count

        self.ships[role.id] = {
            "Total Members": len(member_ids),
            "Total Hosts": len(host_ids),
            "Voyages": voyages_count,
            "Hosted": hosted_count,
            "Ship": self.get_ship_by_role_id(role.id)
        }

    def perc(self, pct, total, abs=True):
        absolute = round(pct / 100. * total)
        if abs:
            return f'{absolute} ({pct:.1f}%)'
        else:
            return f'{pct:.1f}%'

    async def trend_voyages_past_months(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Ship Voyages",
            color=discord.Color.purple(),
            description=f"Report for amount of voyages per month per ship for the last 6 months"
        )

        months = 6
        plt.figure(figsize=(15, 12))
        plt.title('Ship Voyages Trend')
        plt.xlabel('Month')
        plt.ylabel('Voyages')

        for ship in self.ships:
            role = self.bot.get_guild(GUILD_ID).get_role(ship)
            x_dates, y_voyages = [], []

            for month in range(months):
                first_day_of_month = datetime.now().replace(day=1)
                date = first_day_of_month - relativedelta(months=month)
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = (date + relativedelta(months=1)) - timedelta(seconds=1)

                voyages = self.voyage_repository.get_voyages_by_role_ids_and_between_dates(
                    [role.id],
                    start_date,
                    end_date
                )
                voyages = len(voyages) if voyages else 0
                x_dates.append(date)
                y_voyages.append(voyages)

            plt.plot(x_dates, y_voyages, marker='o', label=f"{role.name}", linewidth=2)

        plt.legend()
        file_path = "./ship_voyages_trend.png"
        plt.savefig(file_path)
        plt.close()

        with open(file_path, 'rb') as file:
            discord_file = discord.File(file)
            embed.set_image(url="attachment://ship_voyages_trend.png")

        return embed, discord_file

    async def trend_hosted_past_month(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Ship Hosted",
            color=discord.Color.pink(),
            description=f"Report for amount of hosted per month per ship for the last 6 months"
        )

        months = 6
        plt.figure(figsize=(15, 12))
        plt.title('Ship Hosted Trend')
        plt.xlabel('Month')
        plt.ylabel('Hosted')

        for ship in self.ships:
            role = self.bot.get_guild(GUILD_ID).get_role(ship)
            x_dates, y_hosted = [], []

            for month in range(months):
                first_day_of_month = datetime.now().replace(day=1)
                date = first_day_of_month - relativedelta(months=month)
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = (date + relativedelta(months=1)) - timedelta(seconds=1)

                hosted = self.hosted_repository.get_hosted_by_role_ids_and_between_dates(
                    [role.id],
                    start_date,
                    end_date
                )
                hosted = len(hosted) if hosted else 0
                x_dates.append(date)
                y_hosted.append(hosted)

            plt.plot(x_dates, y_hosted, marker='o', label=f"{role.name}", linewidth=2)

        plt.legend()
        file_path = "./ship_hosted_trend.png"
        plt.savefig(file_path)
        plt.close()

        with open(file_path, 'rb') as file:
            discord_file = discord.File(file)
            embed.set_image(url="attachment://ship_hosted_trend.png")

        return embed, discord_file

    @ships.error
    async def ships_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(embed=error_embed(
                title="Command on cooldown",
                description=f"Please wait {round(error.retry_after)} seconds before using this command again."
            ), ephemeral=True)
        elif isinstance(error, discord.app_commands.errors.MissingAnyRole):
            await interaction.response.send_message(embed=error_embed(
                title="Missing Permissions",
                description="You do not have the required permissions to use this command.",
                footer=False
            ), ephemeral=True)

    def get_ship_by_role_id(self, id):
        for ship in SHIPS:
            if ship.role_id == id:
                return ship
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Ships(bot))