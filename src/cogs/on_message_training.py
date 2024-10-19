from logging import getLogger

from discord.ext import commands

from src.config.training import ALL_TRAINING_RECORDS_CHANNELS
from src.data.repository.training_records_repository import TrainingRecordsRepository
from src.utils.training_utils import process_training_record

log = getLogger(__name__)


class OnMessageTraining(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        training_repository = TrainingRecordsRepository()

        applicable_channel_ids = [channel_id for channel_id in ALL_TRAINING_RECORDS_CHANNELS]

        if message.channel.id in applicable_channel_ids and not message.author.bot:
            log.info(f"[TRAINING] Training record posted in {message.channel.name}.")
            try:
                 await process_training_record(message, message.channel)
                 log.info(f"[TRAINING] Training record {message.id} saved.")
            except Exception as e:
                log.error(f"[TRAINING] Error saving training record: {e}")
            finally:
                training_repository.close_session()

async def setup(bot: commands.Bot):
    await bot.add_cog(OnMessageTraining(bot))
