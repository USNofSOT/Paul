from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.config import NSC_ROLES
from src.data.engine import engine
from src.utils.embeds import default_embed


class DbHealth(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="dbhealth",
        description="View the current health and connection pool status of the database.",
    )
    @app_commands.checks.has_any_role(*NSC_ROLES)
    async def dbhealth(self, interaction: discord.Interaction):
        """Displays database connection pool statistics."""
        pool = engine.pool
        status = pool.status()

        # Parse status string: "Pool size: 20  Connections in pool: 5 Current Overflow: 0 Current Checked out connections: 2"
        # Note: status() returns a string in SQLAlchemy

        embed = default_embed(
            title="Database Pool Health",
            description="Current status of the SQLAlchemy connection pool.",
        )

        embed.add_field(name="Pool Type", value=type(pool).__name__, inline=False)
        embed.add_field(name="Status Raw", value=f"```\n{status}\n```", inline=False)

        # Add some interpretation
        checked_out = pool.checkedout()
        size = pool.size()
        overflow = pool.overflow()
        checked_in = pool.checkedin()

        embed.add_field(name="📤 Checked Out", value=str(checked_out), inline=True)
        embed.add_field(name="😴 In Pool (Idle)", value=str(checked_in), inline=True)
        embed.add_field(name="🏗️ Size Limit", value=str(size), inline=True)
        embed.add_field(name="🌊 Overflow", value=str(overflow), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DbHealth(bot))
