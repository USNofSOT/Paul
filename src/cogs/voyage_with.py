from collections import Counter
from dis import disco
from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config import JE_AND_UP
from src.config.main_server import GUILD_ID, VOYAGE_LOGS
from src.data import SubclassType
from src.data.repository.voyage_repository import VoyageRepository
from src.utils.discord_utils import get_best_display_name
from src.utils.embeds import default_embed
from src.utils.time_utils import format_time, get_time_difference_past

log = getLogger(__name__)

class VoyageWith(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="voyagewith", description="Statistics on how often two users have voyaged together")
    @app_commands.describe(target="The user you want to compare against yourself")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def voyage_together(self, interaction: discord.interactions, target: discord.Member):
        await interaction.response.defer(ephemeral=False)

        voyage_repository = VoyageRepository()
        voyages = voyage_repository.get_incommon_voyages(interaction.user.id, target.id)
        count = len(voyages)

        embed = default_embed(
            title="Voyages with",
            description=f"Information on your voyages with <@{target.id}>",
        )

        embed.add_field(
            name=f":sailboat: Voyages together",
            value=f"{count} times",
            inline=True
        )

        embed.add_field(
            name=":calendar: Last Voyage",
            value=f"{format_time(get_time_difference_past(voyages[0].log_time))} ago",
            inline=True
        )

        times = [voyage.log_time.strftime('%H') for voyage in voyages]
        time_counter = Counter(times)
        most_common_time = time_counter.most_common(1)
        most_common_time_timestamp = most_common_time[0][0]

        embed.add_field(
            name=":clock1: Most common playtime",
            value=f"{most_common_time_timestamp}:00 UTC - {most_common_time[0][1]} times",
            inline=True
        )

        subclasses = [v.hosted.subclasses for v in voyages if v.hosted is not None]
        subclass_counter_me = Counter([subclass.subclass for sublist in subclasses for subclass in sublist if subclass is not None and subclass.target_id == interaction.user.id])
        subclass_counter_target = Counter([subclass.subclass for sublist in subclasses for subclass in sublist if subclass is not None and subclass.target_id == target.id])

        carpenter_emoji = "<:Planks:1256589596473692272>"
        flex_emoji = "<:Sword:1256589612202332313>"
        cannoneer_emoji = "<:Cannon:1256589581894025236>"
        helm_emoji = "<:Wheel:1256589625993068665>"
        grenadier_emoji = "<:AthenaKeg:1030819975730040832>"
        surgeon_emoji = ":adhesive_bandage:"

        subclass_map = {
            SubclassType.CARPENTER: carpenter_emoji,
            SubclassType.FLEX: flex_emoji,
            SubclassType.CANNONEER: cannoneer_emoji,
            SubclassType.HELM: helm_emoji,
            SubclassType.GRENADIER: grenadier_emoji,
            SubclassType.SURGEON: surgeon_emoji
        }

        def get_amount(subclass: SubclassType, target: discord.Member):
            for subclass in subclasses:
                if subclass.target_id == target.id:
                    return subclass.amount

        def get_subclass_type(subclass):
            try:
                return SubclassType(subclass)
            except ValueError:
                return None

        if subclass_counter_me:
            embed.add_field(
                name="Your subclasses",
                value="\n".join(
                    [
                        f"{subclass_map[get_subclass_type(subclass)]} **{get_subclass_type(subclass).name.capitalize()}** - {count}"
                        for subclass, count in subclass_counter_me.items() if get_subclass_type(subclass) is not None
                    ]
                ),
                inline=True
            )

        if target.id != interaction.user.id:
            if subclass_counter_target:
                embed.add_field(
                    name="Their subclasses",
                    value="\n".join(
                        [
                            f"{subclass_map[get_subclass_type(subclass)]} **{get_subclass_type(subclass).name.capitalize()}** - {count}"
                            for subclass, count in subclass_counter_target.items() if
                            get_subclass_type(subclass) is not None
                        ]
                    ),
                    inline=True
                )

        voyages = sorted(voyages, key=lambda v: v.log_time, reverse=True)
        for i in range(0, len(voyages[:5]), 5):
            embed.add_field(
                name="Recent Voyages",
                value="\n".join(
                    [
                        f"Voyage: https://discord.com/channels/{GUILD_ID}/{VOYAGE_LOGS}/{voyage.log_id} - {format_time(get_time_difference_past(voyage.log_time))} ago"
                        for voyage in voyages[i:i + 5]
                    ]
                ),
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=False)



async def setup(bot: commands.Bot):
    await bot.add_cog(VoyageWith(bot))
