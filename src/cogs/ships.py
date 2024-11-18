from datetime import datetime, timedelta
from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config.main_server import GUILD_ID
from src.config.ship_roles import ALL_SHIP_ROLES
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
        self.selected_ship = None
        self.total_voyages = 0

    @app_commands.command(name="ships", description="Get a report of ship activity")
    @app_commands.describe(ship="Optionally provide a ship to get more detailed information about")
    @app_commands.checks.cooldown(1, 60)
    async def ships(self, interaction: discord.Interaction, ship: discord.Role = None):
        self.top_voyagers = {}
        self.top_hosts = {}
        self.top_voyage_ships = {}
        self.top_hosts_ships = {}
        self.ships = {}
        self.selected_ship = None
        self.total_voyages = 0

        try:
            await interaction.response.defer(ephemeral=False)

            if ship and ship.id not in ALL_SHIP_ROLES:
                await interaction.followup.send(embeds=error_embed("Invalid ship"), ephemeral=True)
                return

            self.hosted_repository = HostedRepository()
            self.voyage_repository = VoyageRepository()

            if ship:
                self.selected_ship = ship.id

            # 1. Load in all information
            roles = []
            for role_id in ALL_SHIP_ROLES:
                roles.append(discord.utils.get(interaction.guild.roles, id=role_id))
            for role in roles:
                self.get_info(role)

            # 2. Get the embed for displaying the best performers
            performers_embed = self.get_performers_embed()

            # 3. Get the embed for displaying the ship statistics
            ships_embed = self.get_ships_embed()

            # 4. Check if a ship was provided
            ship_embed = None
            if ship and ship.id in self.ships:
                ship_embed = self.get_ship_embed(ship.id)

            if ship_embed:
                await interaction.followup.send(embeds=[performers_embed, ships_embed, ship_embed])
            else:
                await interaction.followup.send(embeds=[performers_embed, ships_embed])
        except Exception as e:
            log.error(f"Error getting ships: {e}")
            await interaction.followup.send(embed=error_embed("Error getting ships"), ephemeral=True)
        finally:
            self.hosted_repository.close_session()
            self.voyage_repository.close_session()

    def get_performers_embed(self):
        embed = discord.Embed(
            title="Ship Performers Report",
            color=discord.Color.yellow(),
            description=f"Report for ship activity from **{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}** to **{datetime.now().strftime('%Y-%m-%d')}**"
        )

        embed.add_field(name="Total Voyages", value=self.total_voyages, inline=False)

        top_voyagers = {}
        for member_id, voyages in list(self.top_voyagers.items())[:5]:
            member = discord.utils.get(self.bot.get_guild(GUILD_ID).members, id=member_id)
            top_voyagers[member_id] = voyages
        embed.add_field(name=":trophy: Top 5 Voyagers", value="\n".join([f"{index + 1}. <@{member_id}>: \n {voyages} ({round(voyages/self.total_voyages * 100, 1)}%)" for index, (member_id, voyages) in enumerate(top_voyagers.items())]), inline=True)
        top_hosts = {}
        for member_id, hosted in list(self.top_hosts.items())[:5]:
            member = discord.utils.get(self.bot.get_guild(GUILD_ID).members, id=member_id)
            top_hosts[member_id] = hosted
        embed.add_field(name=":trophy: Top 5 Hosts", value="\n".join([f"{index + 1}. <@{member_id}>: \n {hosted} ({round(hosted/self.total_voyages * 100, 1)}%)" for index, (member_id, hosted) in enumerate(top_hosts.items())]), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

        top_voyages = {}
        for ship, voyages in list(self.top_voyage_ships.items())[:5]:
            top_voyages[ship] = voyages
        embed.add_field(name=":ship: Top 5 Voyaging Ships", value="\n".join([f"{index + 1}. <@&{ship}>: \n {voyages} ({round(voyages/self.total_voyages * 100, 1)}%)" for index, (ship, voyages) in enumerate(top_voyages.items())]), inline=True)
        top_hosting = {}
        for ship, hosted in list(self.top_hosts_ships.items())[:5]:
            top_hosting[ship] = hosted
        embed.add_field(name=":ship: Top 5 Hosting Ships", value="\n".join([f"{index + 1}. <@&{ship}>: \n {hosted} ({round(hosted/self.total_voyages * 100, 1)}%)" for index, (ship, hosted) in enumerate(top_hosting.items())]), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Spacer

        return embed


    def get_ships_embed(self):
        embed = discord.Embed(
            title="Ship Statistics Report",
            color=discord.Color.blue(),
            description=f"Report for ship activity from **{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}** to **{datetime.now().strftime('%Y-%m-%d')}**"
        )
        for ship, stats in sorted(self.ships.items(), key=lambda item: item[1]['Voyages'] + item[1]['Hosted'], reverse=True):
            role_name = self.bot.get_guild(GUILD_ID).get_role(int(ship)).name
            embed.add_field(name=f"{role_name}", value=f"Total Members: {stats['Total Members']}\nTotal Hosts: {stats['Total Hosts']}\nVoyages: {stats['Voyages']}\nHosted: {stats['Hosted']}", inline=True)
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

        top_voyagers = {}
        for member_id, voyages in list(self.top_voyagers.items()):
            if member_id in [member.id for member in ship_members]:
                top_voyagers[member_id] = voyages
        embed.add_field(name=":trophy: Top Voyagers", value="\n".join([f"{list(self.top_voyagers.keys()).index(member_id) + 1}. <@{member_id}>: \n {voyages} ({round(voyages / ship['Voyages'] * 100, 1)}%)"for member_id, voyages in top_voyagers.items()][:5]),inline=True)
        top_hosts = {}
        for member_id, hosted in list(self.top_hosts.items()):
            if member_id in [member.id for member in ship_members]:
                top_hosts[member_id] = hosted
        embed.add_field(name=":trophy: Top Hosts", value="\n".join([f"{list(self.top_hosts.keys()).index(member_id) + 1}. <@{member_id}>: \n {hosted} ({round(hosted / ship['Hosted'] * 100, 1)}%)"for member_id, hosted in top_hosts.items()][:5]),inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)  # Spacer

        return embed


    def get_info(self, role: discord.Role) -> None:
        host_ids = []
        member_ids = []

        for member in role.members:
            if any(role.name in ["Voyage Permissions"] for role in member.roles):
                host_ids.append(member.id)
            member_ids.append(member.id)

        hosted = self.hosted_repository.get_hosted_by_target_ids_month_count(host_ids)
        hosted_count = 0
        for host_id in host_ids:
            if host_id in hosted:
                hosted_count += hosted[host_id]


        voyages = self.voyage_repository.get_voyages_by_target_id_month_count(member_ids)
        voyages_count = self.voyage_repository.get_unique_voyages_by_target_id_month_count(member_ids)

        for member_id in member_ids:
            if member_id in voyages:
                self.top_voyagers[member_id] = voyages[member_id]

        self.top_voyagers = dict(sorted(self.top_voyagers.items(), key=lambda item: item[1], reverse=True))

        for host_id in host_ids:
            if host_id in hosted:
                self.top_hosts[host_id] = hosted[host_id]

        self.top_hosts = dict(sorted(self.top_hosts.items(), key=lambda item: item[1], reverse=True))

        self.top_voyage_ships[role.id] = voyages_count
        self.top_hosts_ships[role.id] = hosted_count
        self.top_voyage_ships = dict(sorted(self.top_voyage_ships.items(), key=lambda item: item[1], reverse=True))
        self.top_hosts_ships = dict(sorted(self.top_hosts_ships.items(), key=lambda item: item[1], reverse=True))

        self.total_voyages += hosted_count

        self.ships[role.id] = {
            "Total Members": len(member_ids),
            "Total Hosts": len(host_ids),
            "Voyages": voyages_count,
            "Hosted": hosted_count
        }

    def perc(self, pct, total, abs=True):
        absolute = round(pct / 100. * total)
        if abs:
            return f'{absolute} ({pct:.1f}%)'
        else:
            return f'{pct:.1f}%'

    @ships.error
    async def ships_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(embed=error_embed(
                title="Command on cooldown",
                description=f"Please wait {round(error.retry_after)} seconds before using this command again."
            ), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Ships(bot))