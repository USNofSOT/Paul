from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config import BOA_NSC
from src.data.engine import engine
from src.utils.embeds import default_embed, error_embed

log = getLogger(__name__)


class DBHealth(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="dbhealth", description="Monitor the health of the database connection pool")
    @app_commands.checks.has_any_role(*BOA_NSC)
    async def dbhealth(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            pool = engine.pool
            checked_out = pool.checkedout()
            checked_in = pool.checkedin()
            overflow = pool.overflow()
            pool_size = pool.size()

            # SQLAlchemy QueuePool exposes these attributes
            max_overflow = getattr(pool, "_max_overflow", 0)
            pool_timeout = getattr(pool, "_timeout", 30)
            pool_recycle = getattr(engine, "pool_recycle", -1)
            pool_pre_ping = getattr(engine, "pool_pre_ping", False)

            total_capacity = pool_size + max_overflow
            utilization_pct = (
                (checked_out / total_capacity) * 100 if total_capacity > 0 else 0
            )

            if utilization_pct < 50:
                health_status = f"🟢 Healthy ({utilization_pct:.0f}% utilised)"
                health_color = discord.Color.green()
            elif utilization_pct <= 80:
                health_status = f"🟡 Warning ({utilization_pct:.0f}% utilised)"
                health_color = discord.Color.yellow()
            else:
                health_status = f"🔴 Critical ({utilization_pct:.0f}% utilised)"
                health_color = discord.Color.red()

            embed = default_embed(
                title="Database Connection Pool Health",
                description="Live status of the SQLAlchemy connection pool.",
            )
            embed.color = health_color

            # Section 1: Pool Status
            embed.add_field(name="Pool Size", value=f"`{pool_size}`", inline=True)
            embed.add_field(name="Max Overflow", value=f"`{max_overflow}`", inline=True)
            embed.add_field(name="Pool Timeout", value=f"`{pool_timeout}s`", inline=True)

            # Section 2: Live Counters
            embed.add_field(name="Checked Out", value=f"`{checked_out}`", inline=True)
            embed.add_field(name="Overflow", value=f"`{overflow}`", inline=True)
            embed.add_field(name="Checked In", value=f"`{checked_in}`", inline=True)

            # Section 3: Health Indicator
            embed.add_field(
                name="Health Indicator", value=f"**{health_status}**", inline=False
            )

            # Section 4: Pool Recycle & Pre-Ping
            recycle_str = "Disabled"
            if pool_recycle > 0:
                minutes = pool_recycle // 60
                recycle_str = (
                    f"{minutes} minutes" if minutes > 0 else f"{pool_recycle} seconds"
                )

            embed.add_field(name="Pool Recycle", value=f"`{recycle_str}`", inline=True)
            embed.add_field(
                name="Pre-Ping",
                value="✅ Enabled" if pool_pre_ping else "❌ Disabled",
                inline=True,
            )
            embed.add_field(name="\u200b", value="\u200b", inline=True)

            embed.timestamp = discord.utils.utcnow()

            await interaction.followup.send(embed=embed)

        except Exception as e:
            log.error(f"Error in dbhealth command: {e}", exc_info=True)
            await interaction.followup.send(embed=error_embed(exception=e))


async def setup(bot: commands.Bot):
    await bot.add_cog(DBHealth(bot))
