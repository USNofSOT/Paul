import discord
from discord.ext import commands
from discord import app_commands
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.voyage_repository import VoyageRepository
from logging import getLogger
from src.config.ship_roles import ALL_SHIP_ROLES

log = getLogger(__name__)


class Ships(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.hosted_repository = HostedRepository()
        self.voyage_repository = VoyageRepository()
        self.top_3_voyagers = {}
        self.top_3_hosts = {}
        self.top_3_voyage_ships = {}
        self.ships = {}
        self.total_voyages = 0

    def __del__(self):
        self.hosted_repository.close_session()
        self.voyage_repository.close_session()

    @app_commands.command(name="ships", description="TODO")
    async def ships(self, interaction: discord.Interaction):
        self.top_3_voyagers = {}
        self.top_3_hosts = {}
        self.top_3_voyage_ships = {}
        self.ships = {}
        self.total_voyages = 0

        await interaction.response.defer()
        roles = []
        for role_id in ALL_SHIP_ROLES:
            roles.append(discord.utils.get(interaction.guild.roles, id=role_id))

        for role in roles:
            self.get_info(role)

        embed = discord.Embed(title="Ship Statistics Report", color=discord.Color.yellow())

        embed.add_field(name="Total Voyages", value=self.total_voyages, inline=False)

        top_voyaged = []
        for medal in (":third_place:", ":second_place:", ":first_place:"):
            member_id, voyaged = self.top_3_voyagers.popitem()
            top_voyaged.append(f"{medal} <@{member_id}> with {voyaged}")
        top_voyaged.reverse()
        embed.add_field(name="Top 3 Voyagers :trophy:", value="\n".join(top_voyaged), inline=True)

        top_hosted = []
        for medal in (":third_place:", ":second_place:", ":first_place:"):
            member_id, hosted = self.top_3_hosts.popitem()
            top_hosted.append(f"{medal} <@{member_id}> with {hosted}")
        top_hosted.reverse()
        embed.add_field(name="Top 3 Hosts :trophy:", value="\n".join(top_hosted), inline=True)

        top_ships = []
        for medal in (":third_place:", ":second_place:", ":first_place:"):
            ship, voyages = self.top_3_voyage_ships.popitem()
            top_ships.append(f"{medal} {ship} with {voyages}")
        top_ships.reverse()
        embed.add_field(name="Top 3 Ships :trophy:", value="\n".join(top_ships), inline=True)


        for role_name, role_info in self.ships.items():
            embed.add_field(name=role_name, value=f"Total Members: {role_info['Total Members']}\nTotal Hosts: {role_info['Total Hosts']}\nVoyages: {role_info['Voyages']}\nHosted: {role_info['Hosted']}", inline=True)

        await interaction.followup.send(embed=embed)



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
                self.top_3_voyagers[member_id] = voyages[member_id]

        self.top_3_voyagers = dict(sorted(self.top_3_voyagers.items(), key=lambda item: item[1], reverse=True)[:3])

        for host_id in host_ids:
            if host_id in hosted:
                self.top_3_hosts[host_id] = hosted[host_id]

        self.top_3_hosts = dict(sorted(self.top_3_hosts.items(), key=lambda item: item[1], reverse=True)[:3])

        self.top_3_voyage_ships[role.name] = voyages_count
        self.top_3_voyage_ships = dict(sorted(self.top_3_voyage_ships.items(), key=lambda item: item[1], reverse=True)[:3])

        self.total_voyages += hosted_count

        self.ships[role.name] = {
            "Total Members": len(member_ids),
            "Total Hosts": len(host_ids),
            "Voyages": voyages_count,
            "Hosted": hosted_count
        }



async def setup(bot: commands.Bot):
    await bot.add_cog(Ships(bot))