from asyncio import timeout

import discord
from discord.ext import commands
from discord import app_commands

from src.config import BOA_NSC
from src.data.repository.coin_repository import CoinRepository
from logging import getLogger

log = getLogger(__name__)


class AddAnyCoin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="addanycoin", description="Add coins to a user")
    @app_commands.describe(target="Select the user you want to add coins to")
    @app_commands.describe(coin_name="Name of the Coin you are adding")
    @app_commands.choices(coin_type=[
                                app_commands.Choice(name="Regular Challenge Coin", value="Regular Challenge Coin"),  # Added value
                                app_commands.Choice(name="Commanders Challenge Coin", value="Commanders Challenge Coin")  # Added value
                            ]) 
    @app_commands.checks.has_any_role(*BOA_NSC)
    async def addanycoin(self, interaction: discord.Interaction, target: discord.Member, coin_name: str, coin_type: str): 
        
        # Extract display name (last word as in original logic)
        display_name = coin_type

        # Save the coin transaction using the repository
        coin_repo = CoinRepository()
        try:
            found_coin = (
                coin_repo.find_coin_by_target_and_moderator_and_type
                    (
                        target_id=target.id,
                        moderator_id=interaction.user.id,
                        coin_type=coin_type
                    )
            )
            coin_repo.save_coin(target_id=target.id, coin_type=coin_type, moderator_id=interaction.user.id, old_name=coin_name)
            await interaction.response.send_message(f"Added {coin_type} to {target.display_name or target.name}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while adding the coin. Please try again later.", ephemeral=True)
            log.error(f"Failed to save coin transaction: {e}")
        finally:
            coin_repo.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(AddAnyCoin(bot))
