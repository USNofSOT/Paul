from collections import defaultdict

import discord
from config import JE_AND_UP
from data.repository.coin_repository import CoinRepository
from discord import app_commands
from discord.ext import commands
from utils.embeds import error_embed


async def autocomplete(
    interaction: discord.Interaction, current_input: str
) -> list[app_commands.Choice]:
    coin_repository = CoinRepository()
    coin_givers = {coin.old_name for coin in coin_repository.find()}
    coin_repository.close_session()

    choices = []
    for giver in coin_givers:
        if current_input == "":
            choices.append(app_commands.Choice(name=giver, value=giver))
            continue
        elif giver.lower().startswith(current_input.lower()):
            choices.append(app_commands.Choice(name=giver, value=giver))

    return choices[:25]


class CoinsGiven(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="coins_given", description="Information on coins given by a specific user"
    )
    @app_commands.autocomplete(target=autocomplete)
    @app_commands.describe(target="Name of the user who gave out coins")
    @app_commands.checks.has_any_role(
        *JE_AND_UP,
    )
    async def coins_given(self, interaction: discord.interactions, target: str):
        coin_repository = CoinRepository()
        await interaction.response.defer()

        coins_for_target = coin_repository.find(
            {
                "old_name": target,
            }
        )
        if not coins_for_target:
            await interaction.followup.send(
                embed=error_embed(
                    title="No coins found",
                    description=f"No coins found given out by {target}",
                )
            )
            return

        embed = discord.Embed(
            title=f"Coins given by {target}",
            description=f"Information about the coins given out by {target}",
            color=discord.Color.gold(),
        )

        embed.add_field(
            name="Total coins given",
            value=len(coins_for_target),
            inline=False,
        )

        coins_by_date = defaultdict(list)
        for coin in coins_for_target:
            year_month = coin.coin_time.strftime("%Y-%m")
            coin_info = f"Gave {coin.coin_type} to <@{coin.target_id}> on {coin.coin_time.strftime('%Y-%m-%d')}\n"
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
    await bot.add_cog(CoinsGiven(bot))
