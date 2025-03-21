from collections import defaultdict

import discord
from config import JE_AND_UP
from data.repository.coin_repository import CoinRepository
from discord import app_commands
from discord.ext import commands
from utils.embeds import error_embed


class CoinsReceived(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="coins_received",
        description="Information on coins given by a specific user",
    )
    @app_commands.describe(target="Name of the user who received the coins")
    @app_commands.checks.has_any_role(
        *JE_AND_UP,
    )
    async def coins_given(
        self, interaction: discord.interactions, target: discord.Member = None
    ):
        coin_repository = CoinRepository()
        await interaction.response.defer()

        # If no target is given, default to the author
        if not target:
            target = interaction.user

        coins_for_target = coin_repository.find(
            {
                "target_id": target.id,
            }
        )
        if not coins_for_target:
            await interaction.followup.send(
                embed=error_embed(
                    title="No coins found",
                    description=f"No coins found given to {target}",
                )
            )
            return

        embed = discord.Embed(
            title=f"Coins given to {target}",
            description=f"Information about the coins given to {target}",
            color=discord.Color.gold(),
        )

        embed.add_field(
            name="Total coins given",
            value=len(coins_for_target),
        )

        embed.add_field(
            name="Regular",
            value=len(
                [
                    coin
                    for coin in coins_for_target
                    if coin.coin_type == "Regular Challenge Coin"
                ]
            ),
        )

        embed.add_field(
            name="Commanders",
            value=len(
                [
                    coin
                    for coin in coins_for_target
                    if coin.coin_type == "Commanders Challenge Coin"
                ]
            ),
        )

        coins_by_date = defaultdict(list)
        for coin in coins_for_target:
            year_month = coin.coin_time.strftime("%Y-%m")
            coin_info = f"Received {coin.old_name}'s {coin.coin_type}  on {coin.coin_time.strftime('%Y-%m-%d')}\n"
            coins_by_date[year_month].append(coin_info)

        for year_month, coin_infos in sorted(coins_by_date.items()):
            coins = ""
            for coin_info in coin_infos:
                if len(coins) + len(coin_info) > 1024:
                    embed.add_field(
                        name=f"Coins ({year_month})",
                        value=coins,
                        inline=False,
                    )
                    coins = coin_info
                else:
                    coins += coin_info

            if coins:
                embed.add_field(
                    name=f"Coins ({year_month})",
                    value=coins,
                    inline=False,
                )

        await interaction.followup.send(embed=embed)

        coin_repository.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(CoinsReceived(bot))
