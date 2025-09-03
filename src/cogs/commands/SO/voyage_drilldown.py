from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from src.config import SO_AND_UP
from src.config.main_server import GUILD_ID
from src.config.ranks import RANKS
from src.config.ships import SHIPS
from src.data import engine
from src.utils.embeds import default_embed, error_embed, member_embed
from src.utils.rank_and_promotion_utils import get_current_rank
from src.utils.ship_utils import get_ship_role_id_by_member

log = getLogger(__name__)

Session = sessionmaker(bind=engine)


class VoyageDrilldown(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="voyage_drilldown",
        description="Drill down for a Sailors Voyaging Record (SO+)",
    )
    @app_commands.describe(
        target="Select the user you want to get the voyage record for"
    )
    @app_commands.describe(days="Number of days to look back (default 30)")
    @app_commands.checks.has_any_role(*SO_AND_UP)
    async def voyage_drilldown(
        self,
        interaction: discord.interactions,
        target: discord.Member = None,
        days: int = 30,
    ):
        await interaction.response.defer(ephemeral=True)
        if target is None:
            target = interaction.user

        if days < 1:
            embed = error_embed(
                title="Invalid Days Parameter",
                description="The number of days must be at least 1.",
                footer=False,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        if days > 365:
            embed = error_embed(
                title="Invalid Days Parameter",
                description="The number of days cannot exceed 365.",
                footer=False,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        session = Session()

        results = session.execute(
            text(
                """
                SELECT 
                    v.target_id
                  , v2.target_id AS other_target_id
                  , COUNT(*) AS times_together
                FROM voyages v
                JOIN voyages v2 
                    ON v.log_id = v2.log_id
                   AND v.target_id <> v2.target_id
                WHERE v.log_time >= NOW() - INTERVAL :days DAY
                    AND v.target_id = :target_id
                GROUP BY 
                    v.target_id
                  , v2.target_id
                ORDER BY 
                    v.target_id
                  , times_together DESC;
                """
            ),
            {"target_id": target.id, "days": days},
        ).fetchall()

        if not results:
            embed = error_embed(
                title="No Voyage Records Found",
                description=f"No voyage records found for"
                f" {target.display_name or target.name} in the past {days} days.",
                footer=False,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            session.close()
            return

        # From here we assume we have enough information to display
        embed = member_embed(target)
        embed.title = f"Voyage Drilldown for {target.display_name or target.name}"
        embed.description = f"Voyage records in the past {days} days"

        total_voyages = sum([row[2] for row in results])
        embed.add_field(
            name=":anchor: Total Voyages",
            value=f"**{total_voyages}** voyages with **{len(results)}** unique sailors",
            inline=False,
        )

        top_voyaged_with_embed = default_embed()
        top_voyaged_with: [list] = results[:10]
        if top_voyaged_with:
            top_voyaged_with_embed.title = (
                f"Top Sailors Voyaged With for {target.display_name or target.name}"
            )
            top_voyaged_with_embed.description = (
                f"Voyage records in the past {days} days"
            )

            top_voyaged_with_text = ""
            for index, top in enumerate(top_voyaged_with):
                percentage = (top[2] / total_voyages) * 100
                top_voyaged_with_text += (
                    f"{index + 1}. <@{top[1]}> -"
                    f" **{top[2]}** voyages ({percentage:.2f}%)\n"
                )

            top_voyaged_with_embed.add_field(
                name=":people_holding_hands: Top Sailors Voyaged With",
                value=top_voyaged_with_text,
                inline=False,
            )

        # for each person found in results, check their highest role
        # if any and count how often each rank appears
        rank_count = {}
        for result in results:
            member = self.bot.get_guild(GUILD_ID).get_member(result[1])
            if not member:
                continue
            rank = get_current_rank(member)
            if rank:
                rank_key = (
                    rank.index
                )  # Convert rank to a string to ensure it's hashable
                if rank_key not in rank_count:
                    rank_count[rank_key] = 0
                rank_count[rank_key] += result[2]
                rank.count = rank_count[rank_key]  # Append the count to the rank object

        rank_embed = default_embed()
        if rank_count:
            rank_embed.title = (
                f"Voyages with Rank for {target.display_name or target.name}"
            )
            rank_embed.description = f"Voyage records in the past {days} days"

            # Sort ranks by count (descending)
            sorted_ranks = sorted(
                [rank for rank in RANKS if rank.index in rank_count],
                key=lambda r: -rank_count[r.index],
            )
            rank_text = ""
            for rank in sorted_ranks:
                percentage = (rank_count[rank.index] / total_voyages) * 100
                emoji = rank.emoji if rank.emoji else ""
                rank_text += (
                    f"{emoji} **{rank.name}** - "
                    f"{rank_count[rank.index]} voyages ({percentage:.2f}%)\n"
                )
            rank_embed.add_field(
                name=":military_medal: Voyages by Rank", value=rank_text, inline=False
            )

        ship_count = {}
        for result in results:
            member = self.bot.get_guild(GUILD_ID).get_member(result[1])
            if not member:
                continue
            ship_role_id = get_ship_role_id_by_member(member)
            if ship_role_id:
                if ship_role_id not in ship_count:
                    ship_count[ship_role_id] = 0
                ship_count[ship_role_id] += result[2]

        ship_embed = default_embed()
        if ship_count:
            ship_embed.title = (
                f"Voyages with Ship for {target.display_name or target.name}"
            )
            ship_embed.description = f"Voyage records in the past {days} days"

            # Sort ships by count (descending)
            sorted_ships = sorted(ship_count.items(), key=lambda item: -item[1])
            ship_text = ""
            for ship_role_id, count in sorted_ships:
                ship_role = self.bot.get_guild(GUILD_ID).get_role(ship_role_id)
                # get ship from SHIP list
                ship = next((s for s in SHIPS if s.role_id == ship_role_id), None)
                if ship_role:
                    percentage = (count / total_voyages) * 100
                    ship_text += (
                        f"**{ship_role.name}** - {count} voyages ({percentage:.2f}%)\n"
                        if ship is None
                        else f"**{ship.emoji} {ship_role.name}** - {count} voyages ({percentage:.2f}%)\n"
                    )
            ship_embed.add_field(
                name=":ship: Voyages by Ship", value=ship_text, inline=False
            )

        await interaction.followup.send(
            embeds=[embed, top_voyaged_with_embed, rank_embed, ship_embed],
            ephemeral=True,
        )
        session.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(VoyageDrilldown(bot))
