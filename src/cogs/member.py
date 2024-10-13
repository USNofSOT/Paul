from enum import member
from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config import JE_AND_UP
from src.data import MemberReport, member_report
from src.data.repository.sailor_repository import ensure_sailor_exists
from src.utils.embeds import default_embed, error_embed
from src.utils.time_utils import get_time_difference_past, format_time
from src.utils.report_utils import other_medals, tiered_medals, process_role_index, identify_role_index

log = getLogger(__name__)

def modify_points(base_points: int, force_points: int) -> int:
    return base_points + force_points

class Member(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="member", description="Get information about a member")
    @app_commands.describe(target="Select the user you want to get information about")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def addinfo(self, interaction: discord.interactions, target: discord.Member = None):
        # Set the target to the user running the command if not provided
        if target is None:
            target = interaction.user

        ensure_sailor_exists(target.id)

        embed = default_embed(
            title=f"{target.display_name or target.name}",
            description=f"{target.mention}",
            author=False
        )

        embed.add_field(
            name="Time in Server",
            value=f"{format_time(get_time_difference_past(target.joined_at))}",
        )

        role_index = identify_role_index(interaction, target)
        next_in_command = process_role_index(interaction, target, role_index)

        if len(next_in_command) == 1:
            if next_in_command is None or not isinstance(next_in_command, list):
                embed.add_field(name="Next in Command", value=next_in_command, inline=True)
            else:
                next_in_command = next_in_command[0]
                embed.add_field(name="Next in Command", value=f"<@{next_in_command}>", inline=True)
        elif len(next_in_command) == 2:
            current_member_id = str(next_in_command[1])[1:-1]
            current_member_mention = f"<@{current_member_id}>"
            immediate_member_id = next_in_command[0]
            immediate_member_mention = f"<@{immediate_member_id}>"
            embed.add_field(name="Next in Command",
                               value=f"Current: {current_member_mention}\n Immediate: {immediate_member_mention}",
                               inline=True)
        else:
            next_in_command.add_field(name="Next in Command", value=f"Unknown", inline=True)

        try:
            database_report: MemberReport = member_report(target.id)
        except Exception as e:
            embed = error_embed(exception=e)
            await interaction.followup.send(embed=embed, exception=e)
            return

        embed.add_field(
            name="Other Info",
            value=f"GT: {database_report.sailor.gamertag or 'N/A'}\nTZ: {database_report.sailor.timezone or 'N/A'}",
            inline=True
        )

        if database_report.last_voyage is None:
            last_voyaged = "N/A"
        else:
            last_voyage_format = format_time(get_time_difference_past(database_report.last_voyage))
            if get_time_difference_past(database_report.last_voyage).days >= 30:
                last_voyaged = ":x: " + last_voyage_format
            else:
                last_voyaged = ":white_check_mark: " + last_voyage_format

        embed.add_field(
            name="Last Voyage",
            value=last_voyaged or "N/A",
            inline=True
        )

        embed.add_field(
            name="Average Weekly Voyages",
            value=database_report.average_weekly_voyages,
            inline=True
        )

        total_voyages = database_report.sailor.voyage_count
        # Force voyage count int will act as a modifier
        # If the value is -1 it will subtract from the total voyages
        # If the value is 1 it will add to the total voyages etc.
        if database_report.sailor.force_voyage_count:
            total_voyages += database_report.sailor.force_voyage_count

        embed.add_field(
            name="Total Voyages",
            value=total_voyages,
            inline=True
        )

        if database_report.last_hosted is None:
            last_hosted = "N/A"
        else:
            last_hosted_format = format_time(get_time_difference_past(database_report.last_hosted))
            if get_time_difference_past(database_report.last_hosted).days >= 30:
                last_hosted = ":x: " + last_hosted_format
            else:
                last_hosted = ":white_check_mark: " + last_hosted_format

        embed.add_field(
            name="Last Hosted",
            value=last_hosted or "N/A",
            inline=True
        )

        embed.add_field(
            name="Average Weekly Hosted",
            value=database_report.average_weekly_hosted,
            inline=True
        )

        embed.add_field(
            name="Total Hosted",
            value=database_report.sailor.hosted_count,
            inline=True
        )

        tiered_awards = await tiered_medals(target)

        if tiered_awards != "":
            embed.add_field(name="Tiered Awards", value=tiered_awards, inline=True)
        else:
            embed.add_field(name="Tiered Awards", value="None", inline=True)

        awards_and_titles = await other_medals(target)
        if awards_and_titles:
            formatted = "\n".join(awards_and_titles)
            embed.add_field(name="Awards / Titles", value=formatted, inline=True)
        else:
            embed.add_field(name="Awards / Titles", value="None", inline=True)

        carpenter_emoji = "<:Planks:1256589596473692272>"
        carpenter_points = modify_points(database_report.sailor.carpenter_points, database_report.sailor.force_carpenter_points)

        flex_emoji = "<:Sword:1256589612202332313>"
        flex_points = modify_points(database_report.sailor.flex_points, database_report.sailor.force_flex_points)

        cannoneer_emoji = "<:Cannon:1256589581894025236>"
        cannoneer_points = modify_points(database_report.sailor.cannoneer_points, database_report.sailor.force_cannoneer_points)

        helm_emoji = "<:Wheel:1256589625993068665>"
        helm_points = modify_points(database_report.sailor.helm_points, database_report.sailor.force_helm_points)

        grenadier_emoji = "<:AthenaKeg:1030819975730040832>"
        grenadier_points = modify_points(database_report.sailor.grenadier_points, database_report.sailor.force_grenadier_points)

        surgeon_emoji = ":adhesive_bandage:"
        surgeon_points = modify_points(database_report.sailor.surgeon_points, database_report.sailor.force_surgeon_points)

        embed.add_field(
            name="Subclasses",
            value=f"{carpenter_emoji} Carpenters: {carpenter_points} \n"
                  f"{flex_emoji} Flex: {flex_points} \n"
                  f"{cannoneer_emoji} Cannoneers: {cannoneer_points} \n"
                  f"{helm_emoji} Helm: {helm_points} \n"
                  f"{grenadier_emoji} Grenadiers: {grenadier_points} \n"
                  f"{surgeon_emoji} Surgeons: {surgeon_points}",
            inline = True
        )

        embed.add_field(
            name="Commander's Challenge Coins",
            value="Coming soon...", # TODO
            inline=True
        )

        embed.add_field(
            name="Regular Challenge Coins",
            value="Coming soon...", # TODO
            inline=True
        )

        await interaction.response.send_message(embed=embed)


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
