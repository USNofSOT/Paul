import asyncio
from logging import getLogger, exception
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands

from src.utils.member.user import get_member_embed
from src.config import JE_AND_UP, GUILD_ID, NCO_AND_UP
from src.utils.embeds import error_embed


log = getLogger(__name__)

class Member(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="member", description="Get information about a member")
    @app_commands.describe(target="Select the user you want to get information about")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def addinfo(self, interaction: discord.interactions, target: Union[discord.Member, discord.Role] = None):
        # If no mention is provided, get the information of the user who used the command
        if target is None:
            embed = await get_member_embed(self.bot, interaction, interaction.user)
            log.info(f"Member information requested for self {interaction.user.display_name or interaction.user.name}")
            await interaction.response.send_message(embed=embed)
            return
        else:
            # Check if it's a valid mention
            if not isinstance(target, discord.Member) and not isinstance(target, discord.Role):
                embed = error_embed(
                    title="Invalid Mention",
                    description="Please provide a valid mention.",
                    footer=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Check if user is a user mention or a role mention
        if isinstance(target, discord.Member):
            embed = await get_member_embed(self.bot, interaction, target)
            log.info(f"Member information requested for {target.display_name or target.name}")
            await interaction.response.send_message(embed=embed)
            return


        # Check if it's a role mention
        if isinstance(target, discord.Role):
            role = target
            members = role.members
            channel = self.bot.get_guild(GUILD_ID).get_channel(interaction.channel_id)

            interaction_user_roles = [role.id for role in interaction.user.roles]
            if not any(role in interaction_user_roles for role in JE_AND_UP):
                raise app_commands.errors.MissingAnyRole(JE_AND_UP)

            if len(members) > 30:
                embed = error_embed(
                    title="Too many members",
                    description="Please provide a role with less than 30 members.",
                    footer=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return


            # Check if the role contains the word "squad" or "USS"
            if "squad" not in role.name.lower() and "uss" not in role.name.lower():
                embed = error_embed(
                    title="Invalid Role",
                    description="Please provide a squad or USS role only.",
                    footer=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"Retrieving all members with the role {role.name}",
                    description=f"Processing {len(members)} members, this may take a while.",
                    color=discord.Color.green()
                ),
            )

            for member in members:
                embed = await get_member_embed(self.bot, interaction, member)
                log.info(f"Member information requested for {member.display_name or member.name} with role {role.name}")
                await channel.send(embed=embed)
                await asyncio.sleep(0.25)

            return

        # In case nothing is found return an error
        embed = error_embed(
            title="Invalid Mention",
            description="Please provide a valid mention.",
            footer=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @addinfo.error
    async def addinfo_error(self, interaction: discord.Interaction, error: commands.CommandError):
        log.error(f"Error occurred in addsubclass command: {error}")
        if isinstance(error, app_commands.errors.MissingAnyRole):
            embed = error_embed(
                title="Missing Permissions",
                description="You do not have the required permissions to use this command.",
                footer=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = error_embed(exception=error)
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Member(bot))
