from logging import getLogger

from discord.ext import commands

from src.config.training import ALL_TRAINING_RECORDS_CHANNELS
from src.utils.training_utils import process_training_record

log = getLogger(__name__)


class OnMessageTraining(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        applicable_channel_ids = [channel_id for channel_id in ALL_TRAINING_RECORDS_CHANNELS]

        message_channel = getattr(message, "channel", None)
        channel_id = getattr(message_channel, "id", None)
        author = getattr(message, "author", None)
        if channel_id in applicable_channel_ids and not getattr(author, "bot", False):
            channel_name = getattr(message_channel, "name", f"channel-{channel_id}")
            log.info(f"[TRAINING] Training record posted in {channel_name}.")
            try:
                processed = await process_training_record(message, message_channel)
                if processed:
                    log.info(f"[TRAINING] Training record {message.id} saved.")
                else:
                    log.info(f"[TRAINING] Training record {message.id} skipped.")
            except Exception as e:
                log.error(
                    f"[TRAINING] Error saving training record in {channel_id} for {getattr(author, 'id', 'unknown')}: {e}",
                    exc_info=True,
                    extra={"notify_engineer": True}
                )

async def setup(bot: commands.Bot):
    await bot.add_cog(OnMessageTraining(bot))
