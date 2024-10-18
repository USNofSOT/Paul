import asyncio
from itertools import count
from logging import getLogger
from multiprocessing.managers import Value

from discord.ext import commands

from src.config import GUILD_ID, NRC_RECORDS_CHANNEL, TRAINING_POPULATE_FROM_DATE, NETC_RECORDS_CHANNELS, NETC_GUILD_ID
from src.data.repository.training_records_repository import TrainingRecordsRepository

log = getLogger(__name__)

async def populate_nrc_training_records(bot: commands.Bot, amount: int = 50):
    training_repository = TrainingRecordsRepository()
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(NRC_RECORDS_CHANNEL)
    count = 0
    log.info(f"[TRAINING] Attempting to populate NRC training records from {channel.name}.")
    async for message in channel.history(limit=amount, oldest_first=False, after=TRAINING_POPULATE_FROM_DATE):

        try:
            training_repository.save_training(log_id=message.id, target_id=message.author.id, log_channel_id=channel.id, log_time=message.created_at)
        except ValueError as e:
            log.warning(f"[TRAINING] Skipping training record {message.id} as it already exists.")
            continue

        count += 1
        log.info(f"[TRAINING] Processed NRC training record #{count}.")
        await asyncio.sleep(1)

    log.info("[TRAINING] Finished populating NRC training records.")
    training_repository.close_session()

async def populate_netc_training_records(bot: commands.Bot, amount: int = 50):
    training_repository = TrainingRecordsRepository()
    guild = bot.get_guild(NETC_GUILD_ID)
    channels = [channel_id for channel_id in NETC_RECORDS_CHANNELS]
    print(channels)
    for channel in channels:
        channel = guild.get_channel(channel)
        count = 0
        log.info(f"[TRAINING] Attempting to populate NETC training records from {channel.name}.")
        async for message in channel.history(limit=amount, oldest_first=False, after=TRAINING_POPULATE_FROM_DATE):

            try:
                training_repository.save_training(log_id=message.id, target_id=message.author.id, log_channel_id=channel.id, log_time=message.created_at)
            except ValueError as e:
                log.warning(f"[TRAINING] Skipping training record {message.id} as it already exists.")
                continue

            count += 1
            log.info(f"[TRAINING] Processed NETC training record from {channel.name} #{count}.")
            await asyncio.sleep(1)

        log.info(f"[TRAINING] Finished populating NETC training records from {channel.name}.")
    log.info("[TRAINING] Finished populating NETC training records.")