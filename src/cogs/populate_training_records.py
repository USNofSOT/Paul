from logging import getLogger

import discord.ext.commands
from discord.ext import commands

from src.config import NSC_ROLES
from src.utils.training_utils import populate_nrc_training_records, populate_netc_training_records

log = getLogger(__name__)

class PopulateTrainingRecords(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="populate_training_records")
    @commands.has_any_role(*NSC_ROLES)
    async def populate_voyages(self, context, amount: int = 50, nrc: bool = True, netc: bool = True):
        if amount == -1:
            max_voyages = None
        else:
            max_voyages = amount

        # The following feature was removed from the bot.
        # if roles:
        #     log.info(f"[TRAINING] Attempting to populate Graduate roles.")
        #     await context.send("Attempting to populate Graduate roles.")
        #     await populate_graduate_roles(self.bot)
        #     await context.send("Finished populating Graduate roles.")

        if nrc:
            log.info(f"[TRAINING] Attempting to populate NRC training records.")
            await context.send("Attempting to populate NRC training records.")
            await populate_nrc_training_records(self.bot, amount=max_voyages)
            await context.send("Finished populating NRC training records.")

        if netc:
            await context.send("Attempting to populate NETC training records.")
            await populate_netc_training_records(self.bot, amount=max_voyages)
            await context.send("Finished populating NETC training records.")
            log.info("[TRAINING] Finished populating training records.")

        await context.send("Finished populating training records.")


async def setup(bot: commands.Bot):
    await bot.add_cog(PopulateTrainingRecords(bot))
