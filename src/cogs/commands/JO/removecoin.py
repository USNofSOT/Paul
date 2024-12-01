import discord
from attr.validators import optional
from discord.ext import commands
from discord import app_commands

from src.config import JO_AND_UP, BOA_ROLE, NCO_AND_UP, BOA_NSC
from src.data.repository.coin_repository import CoinRepository
from src.data.repository.coin_repository import Coins
from logging import getLogger

log = getLogger(__name__)

class ConfirmationViewRemCoin(discord.ui.View):
    def __init__(self, issuer: discord.Member, target: discord.Member, coin_type: str, found_coin: Coins):
        super().__init__(timeout=60)
        self.issuer = issuer
        self.target = target
        self.coin_type = coin_type
        self.found_coin = found_coin

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        coin_repo = CoinRepository()
        try:
            coin_repo.remove_coin(self.found_coin)
            await interaction.response.send_message(
                f"Removed {self.coin_type} from {self.target.display_name or self.target.name}",
                ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while removing the coin. Please try again later.",
                                                    ephemeral=True)
            log.error(f"Failed to remove coin transaction: {e}")
            return
        finally:
            coin_repo.close_session()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Action cancelled.", ephemeral=True)
        self.stop()



class RemoveCoin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot



    @app_commands.command(name="removecoin", description="Remove coin from a user")
    @app_commands.describe(target="Select the user you want to remove coins from")
    @app_commands.choices(coin_type=[
        discord.app_commands.Choice(name="Regular Challenge Coin", value="Regular Challenge Coin"),
        discord.app_commands.Choice(name="Commanders Challenge Coin", value="Commanders Challenge Coin")
    ])
    @app_commands.checks.has_any_role(*JO_AND_UP)
    async def removecoin(self, interaction: discord.Interaction, target: discord.Member = None, coin_type: str = None):
        # Set the target to the user running the command if not provided
        if target is None:
            target = interaction.user

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
            if not found_coin:
                log.info(
                    f"Attempted to remove non-existent coin from {target.display_name or target.name} by {interaction.user.display_name or interaction.user.name}"
                )
                await interaction.response.send_message(
                    f"{target.display_name or target.name} does not have a coin from {interaction.user.display_name or interaction.user.name}",
                    ephemeral=True)
                return

            view = ConfirmationViewRemCoin(issuer=interaction.user, target=target, coin_type=coin_type,
                                           found_coin=found_coin)
            await interaction.response.send_message(
                f"Are you sure you want to remove {coin_type} from {target.display_name or target.name}?", view=view,
                ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("An error occurred while removing the coin. Please try again later.", ephemeral=True)
            log.error(f"Failed to remove coin transaction: {e}")
            return
        finally:
            coin_repo.close_session()

    @app_commands.command(name="removeanycoin", description="Remove coin from a user given by someone")
    @app_commands.describe(target="Select the user you want to remove coins from")
    @app_commands.describe(issuer="Select the user you want to remove coins from")
    @app_commands.choices(coin_type=[
        discord.app_commands.Choice(name="Regular Challenge Coin", value="Regular Challenge Coin"),
        discord.app_commands.Choice(name="Commanders Challenge Coin", value="Commanders Challenge Coin")
    ])
    @app_commands.checks.has_any_role(*BOA_NSC)
    async def removeanycoin(self, interaction: discord.Interaction, target: discord.Member = None, issuer: discord.Member = None, coin_type: str = None):
        if target is None:
            target = interaction.user

        if issuer is None:
            issuer = interaction.user

        coin_repo = CoinRepository()

        try:
            found_coin = (
                coin_repo.find_coin_by_target_and_moderator_and_type
                    (
                        target_id=target.id,
                        moderator_id=issuer.id,
                        coin_type=coin_type
                    )
            )
            if not found_coin:
                log.info(
                    f"Attempted to remove non-existent coin from {target.display_name or target.name} by {issuer.display_name or issuer.name}"
                )
                await (interaction.response.send_message(
                    f"{target.display_name or target.name} does not have a {coin_type} from {issuer.display_name or issuer.name}",
                    ephemeral=True))
                return

            view = ConfirmationViewRemCoin(issuer=issuer, target=target, coin_type=coin_type,
                                           found_coin=found_coin)
            await interaction.response.send_message(
                f"Are you sure you want to remove {coin_type} from {target.display_name or target.name}, issued by {issuer.display_name or issuer.name}?",
                view=view, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while removing the coin. Please try again later.",
                                                    ephemeral=True)
            log.error(f"Failed to remove coin transaction: {e}")
            return
        finally:
            coin_repo.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(RemoveCoin(bot))
