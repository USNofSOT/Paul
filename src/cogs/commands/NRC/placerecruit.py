from logging import getLogger
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import GUILD_ID, NRC_ROLE, SHIP_COS_ROLE
from config.ships import SHIP_MAX_SIZE, SHIPS, FLEETS_OF_THE_NAVY

log = getLogger(__name__)


class PlaceRecruit(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="placerecruit", description="Determine ship placement for a recruit")
    @app_commands.describe(target="Select the user who recruited them")
    @app_commands.checks.has_any_role(NRC_ROLE)
    async def placerecruit(self, interaction: discord.Interaction, target: Optional[discord.Member] = None): 
        guild = self.bot.get_guild(GUILD_ID)
        ship_roles = {ship.role_id : guild.get_role(ship.role_id) for ship in SHIPS}

        # If no target, return the ship with the lowest headcount
        if target is None:
            min_ship = await self._min_ship(guild)
            msg = f"The {min_ship.mention} has the lowest headcount, at {len(min_ship.members)}/{SHIP_MAX_SIZE} members."
            msg += await self.formatted_msg(min_ship, guild)
            await interaction.response.send_message(msg, ephemeral=True)
            return
        
        # If target not assigned to any ships, return lowest in Navy
        target_ship_roles = [ship_roles[role.id] for role in target.roles if role.id in ship_roles]
        if not target_ship_roles:
            min_ship = await self._min_ship(guild)
            msg = f"{target.mention} is not assigned to a ship. The {min_ship.mention} has the lowest headcount, at {len(min_ship.members)}/{SHIP_MAX_SIZE} members."
            msg += await self.formatted_msg(min_ship, guild)
            await interaction.response.send_message(msg, ephemeral=True)
            return

        # Suggest each non-full ship the target is a part of
        msg_strs = []
        for ship_role in target_ship_roles:
            count = len(ship_role.members)
            if count < SHIP_MAX_SIZE:
                msg = f"{target.mention} is on the {ship_role.mention}, which has {count}/{SHIP_MAX_SIZE} members."
                msg_strs.append(msg)
        if msg_strs:
            msg = ' Additionally, '.join(msg_strs)
            for ship_role in target_ship_roles:
                msg += await self.formatted_msg(ship_role, guild)
            await interaction.response.send_message(msg, ephemeral=True)
            return

        # Suggest the lowest ships in the target's fleet(s)
        min_count = SHIP_MAX_SIZE + 1
        msg_strs = []
        target_fleet_roles = []
        fmtd_strs = []
        for fleet in FLEETS_OF_THE_NAVY.fleets:
            fleet_role = guild.get_role(fleet.role_id)
            if fleet_role in target.roles:
                for ship in fleet.ships:
                    ship_role = ship_roles[ship.role_id]
                    count = len(ship_role.members)
                    msg = f"{target.mention} is on "
                    if len(target_ship_roles) == 1:
                        msg += "a full ship. "
                    else:
                        msg += "full ships. "
                    msg += f"{target.mention} is in {fleet_role.mention}, "
                    msg += f"where the {ship_role.mention} has the lowest head count, "
                    msg += f"at {len(ship_role.members)}/{SHIP_MAX_SIZE} members."
                    if count == min_count:
                        msg_strs.append(msg)
                        fmtd_strs.append(await self.formatted_msg(ship_role, guild))
                    elif count < min_count and count < SHIP_MAX_SIZE:
                        min_count = count
                        msg_strs = [msg]
                        fmtd_strs = [await self.formatted_msg(ship_role, guild)]
                target_fleet_roles.append(fleet_role)
        if msg_strs:
            msg = ' Additionally, '.join(msg_strs) + ''.join(fmtd_strs)
            await interaction.response.send_message(msg, ephemeral=True)
            return

        # Otherwise, return the ship with the lowest head cont
        min_ship = await self._min_ship(guild)
        msg = f"{target.mention} is in "
        if len(target_fleet_roles) == 1:
            msg += "a full fleet. "
        else:
            msg += "full fleets. "
        msg += f"The {min_ship.mention} has the lowest headcount, at {len(min_ship.members)}/{SHIP_MAX_SIZE} members."
        msg += await self.formatted_msg(min_ship, guild)
        await interaction.response.send_message(msg, ephemeral=True)
        return

    async def _min_ship(self, guild : discord.Guild) -> discord.Role:
        ship_roles = [guild.get_role(ship.role_id) for ship in SHIPS]

        min_count = 0
        min_role = None
        for idx, role in enumerate(ship_roles):
            n_members = len(role.members)
            if idx == 0 or n_members < min_count:
                min_count = n_members
                min_role = role
        return min_role
    
    async def formatted_msg(self, ship : discord.Role, guild : discord.Guild) -> str:
        msg = "\n\n"

        # ship
        msg += f"Ship: {ship.mention}\n"

        # fleet
        fleet_found = False
        for fleet in FLEETS_OF_THE_NAVY.fleets:
            role_ids = [ship.role_id for ship in fleet.ships]
            if ship.id in role_ids:
                msg += f"Fleet: {guild.get_role(fleet.role_id).mention}\n"
                fleet_found = True
                break
        if not fleet_found:
            msg += f"Fleet: Not Found\n"

        # chief of ship
        cos_found = False
        for member in ship.members:
            member_roles = member.roles
            for role in member_roles:
                if role.id == SHIP_COS_ROLE:
                    msg += f"Chief of Ship: {member.mention}\n"
                    cos_found = True
                    break
        if not cos_found:
            msg += "Chief of Ship: Not Found\n"

        return msg
        

async def setup(bot: commands.Bot):
    await bot.add_cog(PlaceRecruit(bot))
