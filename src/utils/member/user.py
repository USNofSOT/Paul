import discord
from config.ranks import DECKHAND
from discord.ext.commands import Bot
import io
from logging import getLogger
from PIL import Image

from src.config import COIN_IDS, NCO_AND_UP
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


log = getLogger(__name__)


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
    if current_rank is None:
        current_rank = DECKHAND
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

    tiered_awards, _ = await tiered_medals(member)
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


async def get_ribbon_board_embed(bot: Bot, interaction, member: discord.Member) -> tuple[discord.Embed, discord.File]:
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
    
    _, tiered_roles = await tiered_medals(member)
    _, awards_and_titles_roles = await other_medals(member)

    # check for challenge coins
    CC_roles = [role for role in member.roles if role.id in COIN_IDS]

    # Assemble awards, fix for order of precedence
    award_roles = awards_and_titles_roles + tiered_roles + CC_roles
    if tiered_roles and 'Service Stripes' in tiered_roles[-1].name:
        award_roles = awards_and_titles_roles + tiered_roles[:-1] + CC_roles + [tiered_roles[-1]]

    if not award_roles:
        log.info(f"No award roles found for {member.name}.")
        return embed
    
    # FIXME: retrieving image data from discord on each call is slow
    # It would be faster to store the ribbon images in the repo
    award_images = []
    session = bot.http._HTTPClient__session
    for role in award_roles:
        log.info(f"Requesting image for {role.name}.")
        if role.display_icon:
            async with session.get(role.display_icon.url) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    award_images.append(Image.open(io.BytesIO(img_data)))
                else:
                    award_images.append(None)
        else:
            award_images.append(None)
    images = [img for img in award_images if img is not None]
    board_roles = [role for role,img in zip(award_roles,award_images) if img is not None]

    if not images:
        log.info(f"No award images found for {member.name}, despite having award roles.")
        return embed
    log.info("Gathered all ribbon images.")
    
    awards_str = '1. '
    row_num = 1

	# Arrange images in a grid
    columns = 3
    img_height = 64  # Fixed height for all ribbons
    spacing = 5
    aspect_ratio = images[0].width / images[0].height  # Assume all images have the same aspect ratio
    img_width = int(img_height * aspect_ratio)  # Calculate proportional width

    rows = (len(images) + columns - 1) // columns
    top_row_ribbons = len(images) % columns  # Check how many ribbons are in the first row

    canvas_width = (columns * img_width) + ((columns - 1) * spacing)
    canvas_height = (rows * img_height) + ((rows - 1) * spacing)
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))  # Transparent background

    x = 0
    y = 0
    if top_row_ribbons:
        offset_x = canvas_width - top_row_ribbons*img_width - (top_row_ribbons-1)*spacing
        offset_x //= 2
        x = offset_x
        for index in range(top_row_ribbons):
            img = images[index].resize((img_width, img_height))
            canvas.paste(img, (x, y), img)
            x += img_width + spacing

            awards_str += f"{board_roles[index].name}"
            if index < (top_row_ribbons - 1):
                awards_str += ', '
            else:
                awards_str += '\n'
        x = 0
        y = img_height + spacing
        row_num += 1
        awards_str += f"{row_num}. "

    k = 0
    for index in range(top_row_ribbons, len(images)):
        img = images[index].resize((img_width, img_height))
        canvas.paste(img, (x, y), img)
        awards_str += f"{board_roles[index].name}"
        k += 1
        if k < columns:
            x += img_width + spacing
            awards_str += ', '
        else:
            k = 0
            x = 0
            y += img_height + spacing
            awards_str += '\n'
            if index < len(images) - 1:
                row_num += 1
                awards_str += f"{row_num}. "


    # Convert to byte stream for Discord upload
    image_bytes = io.BytesIO()
    canvas.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    file = discord.File(image_bytes, filename="ribbons.png")

    # Add ribbon board to embed
    embed.set_image(url=f"attachment://ribbons.png")
    
    # Add role for each
    embed.add_field(name="Awards", value=awards_str, inline=True)

    log.info('reached end of get_ribbon_board_embed')
    return embed, file
