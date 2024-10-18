from logging import getLogger

import discord
from discord.ext import commands

from src.config import ALL_TRAINING_RECORDS_CHANNELS
from src.data.repository.training_records_repository import TrainingRecordsRepository

log = getLogger(__name__)


class OnDeleteTraining(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_delete(self, message: discord.RawMessageDeleteEvent):
        training_repository = TrainingRecordsRepository()

        applicable_channel_ids = [channel_id for channel_id in ALL_TRAINING_RECORDS_CHANNELS]

        if message.channel_id in applicable_channel_ids:
            log.info(f"[TRAINING] Training record deleted in {message.channel_id}.")
            try:
                training_repository.delete_training(log_id=message.message_id, log_channel_id=message.channel_id)
                log.info(f"[TRAINING] Training record {message.message_id} deleted.")
            except Exception as e:
                log.error(f"[TRAINING] Error deleting training record: {e}")
            finally:
                training_repository.close_session()

async def setup(bot: commands.Bot):
    await bot.add_cog(OnDeleteTraining(bot))
