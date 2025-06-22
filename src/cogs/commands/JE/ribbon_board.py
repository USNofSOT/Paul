import asyncio
from logging import getLogger
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands

from src.config import JE_AND_UP, VT_ROLES, RT_ROLES
from src.utils.embeds import error_embed
from src.utils.member.user import get_ribbon_board_embed

log = getLogger(__name__)

class RibbonBoard(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="ribbon_board", description="Get ribbon board for a member")
    @app_commands.describe(target="Select the user you want to get the ribbon board for")
    @app_commands.checks.has_any_role(*JE_AND_UP, *VT_ROLES, *RT_ROLES)
    async def ribbon_board(self, interaction: discord.interactions, target: Union[discord.Member, discord.Role] = None):
        await interaction.response.defer()
        # If no mention is provided, get the information of the user who used the command
        if target is None:
            embed, file = await get_ribbon_board_embed(self.bot, interaction, interaction.user)
            log.info(f"Ribbon board requested for self {interaction.user.display_name or interaction.user.name}")
            await interaction.followup.send(embed=embed, file=file)
            return
        else:
            # Check if it's a valid mention
            if not isinstance(target, discord.Member) and not isinstance(target, discord.Role):
                embed = error_embed(
                    title="Invalid Mention",
                    description="Please provide a valid mention.",
                    footer=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        # Check if user is a user mention or a role mention
        if isinstance(target, discord.Member):
            embed, file = await get_ribbon_board_embed(self.bot, interaction, target)
            log.info(f"Ribbon board requested for {target.display_name or target.name}")
            await interaction.followup.send(embed=embed, file=file)
            return


        # Check if it's a role mention
        if isinstance(target, discord.Role):
            role = target
            members = role.members

            interaction_user_roles = [role.id for role in interaction.user.roles]
            if not any(role in interaction_user_roles for role in JE_AND_UP):
                raise app_commands.errors.MissingAnyRole(JE_AND_UP)

            if len(members) > 30:
                embed = error_embed(
                    title="Too many members",
                    description="Please provide a role with less than 30 members.",
                    footer=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"Retrieving all members with the role {role.name}",
                    description=f"Processing {len(members)} members, this may take a while.",
                    color=discord.Color.green()
                ),
            )

            for member in members:
                embed, file = await get_ribbon_board_embed(self.bot, interaction, member)
                log.info(f"Ribbon board requested for {member.display_name or member.name} with role {role.name}")
                await interaction.channel.send(embed=embed, file=file)
                await asyncio.sleep(0.5)
            return

        # In case nothing is found return an error
        embed = error_embed(
            title="Invalid Mention",
            description="Please provide a valid mention.",
            footer=False
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @ribbon_board.error
    async def ribbon_board_error(self, interaction: discord.Interaction, error: commands.CommandError):
        log.error(f"Error occurred in member command: {error}")
        if isinstance(error, app_commands.errors.MissingAnyRole):
            embed = error_embed(
                title="Missing Permissions",
                description="You do not have the required permissions to use this command.",
                footer=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = error_embed(exception=error)

async def setup(bot: commands.Bot):
    await bot.add_cog(RibbonBoard(bot))
