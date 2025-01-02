from asyncio import timeout

import discord
from discord.ext import commands
from discord import app_commands

from src.config import JO_AND_UP
from src.data.repository.coin_repository import CoinRepository
from logging import getLogger

log = getLogger(__name__)


class AddCoin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="addcoin", description="Add coins to a user")
    @app_commands.describe(target="Select the user you want to add coins to")
    @app_commands.checks.has_any_role(*JO_AND_UP)
    async def addcoin(self, interaction: discord.Interaction, target: discord.Member):
        # If target is None, set target to the author of the interaction
        if target is None:
            target = interaction.user

        # Get the coin type from the interaction
        if any(role.name in ["Senior Officer"] for role in interaction.user.roles):
            coin_type = "Commanders Challenge Coin"
        else:
            coin_type = "Regular Challenge Coin"

        # Extract display name (last word as in original logic)
        display_name = interaction.user.display_name.split()[-1]

        # Save the coin transaction using the repository
        coin_repo = CoinRepository()
        try:
            found_coin = (
                coin_repo.find_coin_by_target_and_OldName_and_type
                    (
                        target_id=target.id,
                        old_name=display_name,
                        coin_type=coin_type
                    )
            )
            if found_coin:
                log.info(f"Attempted to add existing {coin_type} to {target.display_name or target.name} from {interaction.user.display_name or interaction.user.name}")
                await interaction.response.send_message(f"{target.display_name or target.name} already has a {coin_type} from {interaction.user.display_name or interaction.user.name}", ephemeral=True)
                return
            coin_repo.save_coin(target_id=target.id, coin_type=coin_type, moderator_id=interaction.user.id, old_name=display_name)
            await interaction.response.send_message(f"Added {coin_type} to {target.display_name or target.name}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while adding the coin. Please try again later.", ephemeral=True)
            log.error(f"Failed to save coin transaction: {e}")
        finally:
            coin_repo.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(AddCoin(bot))
