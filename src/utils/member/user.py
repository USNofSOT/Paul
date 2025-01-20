import discord
from discord.ext.commands import Bot

from src.config import GUILD_OWNER_ID, NCO_AND_UP
from src.config.main_server import GUILD_ID
from src.config.requirements import (
    HOSTING_REQUIREMENT_IN_DAYS,
    VOYAGING_REQUIREMENT_IN_DAYS,
)
from src.data import MemberReport, RoleChangeType, member_report
from src.data.repository.auditlog_repository import AuditLogRepository
from src.data.repository.coin_repository import CoinRepository
from src.data.repository.sailor_repository import ensure_sailor_exists
from src.data.structs import NavyRank, SailorCO
from src.utils.embeds import default_embed, error_embed
from src.utils.rank_and_promotion_utils import get_current_rank
from src.utils.report_utils import (
    other_medals,
    tiered_medals,
)
from src.utils.time_utils import format_time, get_time_difference_past


def modify_points(base_points: int, force_points: int) -> int:
    return base_points + force_points

async def get_member_embed(bot: Bot, interaction, member: discord.Member) -> discord.Embed:
    ensure_sailor_exists(member.id)

    # Get the appropriate avatar URL

    embed = default_embed(
        title=f"{member.display_name or member.name}",
        description=f"{member.mention}",
        author=False
    )

    try:
        avatar_url = member.guild_avatar.url if member.guild_avatar else member.avatar.url
        embed.set_thumbnail(url=avatar_url)
    except AttributeError:
        pass

    audit_log_repository = AuditLogRepository()
    current_rank: NavyRank = get_current_rank(member)
    current_rank_role_id = next((role.id for role in member.roles if role.id in current_rank.role_ids), None)

    rank_audit_log = audit_log_repository.get_latest_role_log_for_target_and_role(member.id, current_rank_role_id)
    ranked_at = format_time(get_time_difference_past(rank_audit_log.log_time)) if rank_audit_log else ""
    if rank_audit_log is not None and rank_audit_log.change_type == RoleChangeType.REMOVED:
        ranked_at = ""

    embed.add_field(
        name="Time in Server",
        value=f"{format_time(get_time_difference_past(member.joined_at))} \n {'**Time in Rank** \n' + ranked_at if ranked_at else ''}",
    )

    audit_log_repository.close_session()

    # Add Next in Command
    guild = bot.get_guild(GUILD_ID)
    co_str = SailorCO(member, guild).member_str
    embed.add_field(name="Next in Command", value=co_str, inline=True)

    ## Add Member Report
    try:
        database_report: MemberReport = member_report(member.id)
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
        if get_time_difference_past(database_report.last_voyage).days >= VOYAGING_REQUIREMENT_IN_DAYS:
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

    total_voyages = modify_points(database_report.sailor.voyage_count, database_report.sailor.force_voyage_count)
    total_voyages_display = f"{total_voyages} ({database_report.sailor.voyage_count})" if database_report.sailor.force_voyage_count != 0 else str(total_voyages)

    embed.add_field(
        name="Total Voyages",
        value=total_voyages_display,
        inline=True
    )

    if database_report.last_hosted is None:
        last_hosted = "N/A"
    else:
        last_hosted_format = format_time(get_time_difference_past(database_report.last_hosted))
        if get_time_difference_past(database_report.last_hosted).days >= HOSTING_REQUIREMENT_IN_DAYS:
            last_hosted = ":x: " + last_hosted_format
        else:
            last_hosted = ":white_check_mark: " + last_hosted_format

    total_hosted = modify_points(database_report.sailor.hosted_count, database_report.sailor.force_hosted_count)
    total_hosted_display = f"{total_hosted} ({database_report.sailor.hosted_count})" if database_report.sailor.force_hosted_count != 0  else str(total_hosted)

    interaction_user_roles = [role.id for role in member.roles]
    if any(role in interaction_user_roles for role in NCO_AND_UP):
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
            value=total_hosted_display,
            inline=True
        )

    carpenter_emoji = "<:Planks:1256589596473692272>"
    carpenter_points = modify_points(database_report.sailor.carpenter_points, database_report.sailor.force_carpenter_points)
    carpenter_points_display = f"{carpenter_points} ({database_report.sailor.carpenter_points})" if database_report.sailor.force_carpenter_points != 0  else str(carpenter_points)

    flex_emoji = "<:Sword:1256589612202332313>"
    flex_points = modify_points(database_report.sailor.flex_points, database_report.sailor.force_flex_points)
    flex_points_display = f"{flex_points} ({database_report.sailor.flex_points})" if database_report.sailor.force_flex_points != 0  else str(flex_points)

    cannoneer_emoji = "<:Cannon:1256589581894025236>"
    cannoneer_points = modify_points(database_report.sailor.cannoneer_points, database_report.sailor.force_cannoneer_points)
    cannoneer_points_display = f"{cannoneer_points} ({database_report.sailor.cannoneer_points})" if database_report.sailor.force_cannoneer_points != 0  else str(cannoneer_points)

    helm_emoji = "<:Wheel:1256589625993068665>"
    helm_points = modify_points(database_report.sailor.helm_points, database_report.sailor.force_helm_points)
    helm_points_display = f"{helm_points} ({database_report.sailor.helm_points})" if database_report.sailor.force_helm_points != 0  else str(helm_points)

    grenadier_emoji = "<:AthenaKeg:1030819975730040832>"
    grenadier_points = modify_points(database_report.sailor.grenadier_points, database_report.sailor.force_grenadier_points)
    grenadier_points_display = f"{grenadier_points} ({database_report.sailor.grenadier_points})" if database_report.sailor.force_grenadier_points != 0  else str(grenadier_points)

    surgeon_emoji = ":adhesive_bandage:"
    surgeon_points = modify_points(database_report.sailor.surgeon_points, database_report.sailor.force_surgeon_points)
    surgeon_points_display = f"{surgeon_points} ({database_report.sailor.surgeon_points})" if database_report.sailor.force_surgeon_points != 0  else str(surgeon_points)

    embed.add_field(
        name="Subclasses",
        value=f"{carpenter_emoji} Carpenter: {carpenter_points_display} \n"
              f"{flex_emoji} Flex: {flex_points_display} \n"
              f"{cannoneer_emoji} Cannoneer: {cannoneer_points_display} \n"
              f"{helm_emoji} Helm: {helm_points_display} \n"
              f"{grenadier_emoji} Grenadier: {grenadier_points_display} \n"
              f"{surgeon_emoji} Surgeon: {surgeon_points_display}",
        inline=True
    )

    coin_repository = CoinRepository()
    # Get coins
    regular_coins, commander_coins = coin_repository.get_coins_by_target(member.id)

    embed.add_field(
        name="Commander's Coins",
        value="\n".join([str(coin.old_name + "'s Coin") for coin in commander_coins[:5]]) + (
            f"\n...and {len(commander_coins) - 5} more coins" if len(commander_coins) > 5 else "") or "None",
        inline=True
    )

    embed.add_field(
        name="Regular Coins",
        value="\n".join([str(coin.old_name + "'s Coin") for coin in regular_coins[:5]]) + (
            f"\n...and {len(regular_coins) - 5} more coins" if len(regular_coins) > 5 else "") or "None",
        inline=True
    )

    tiered_awards = await tiered_medals(member)
    if tiered_awards != "":
        embed.add_field(name="Tiered Awards", value=tiered_awards, inline=True)
    else:
        embed.add_field(name="Tiered Awards", value="None", inline=True)

    awards_and_titles, awards_and_titles_roles = await other_medals(member)
    if awards_and_titles:
        formatted = "\n".join([f"<@&{award.id}>" for award in awards_and_titles_roles])
        embed.add_field(name="Awards / Titles", value=formatted, inline=True)
    else:
        embed.add_field(name="Awards / Titles", value="None", inline=True)

    coin_repository.close_session()
    return embed
