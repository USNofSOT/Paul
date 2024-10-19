import asyncio
from logging import getLogger

from discord.ext import commands
from typing_extensions import deprecated

from src.config.main_server import NRC_RECORDS_CHANNEL, GUILD_ID
from src.config.netc_server import NETC_GUILD_ID, SNLA_GRADUATE_ROLE, JLA_GRADUATE_ROLE, OCS_GRADUATE_ROLE, \
    SOCS_GRADUATE_ROLE, NETC_RECORDS_CHANNELS
from src.config.training import TRAINING_POPULATE_FROM_DATE
from src.data.repository.training_records_repository import TrainingRecordsRepository

log = getLogger(__name__)

# The following function is no longer in used; this feature was removed from the bot.
# async def populate_graduate_roles(bot: commands.Bot):
#     guild = bot.get_guild(NETC_GUILD_ID)
#     graduate_roles = [guild.get_role(role) for role in [JLA_GRADUATE_ROLE, SNLA_GRADUATE_ROLE, OCS_GRADUATE_ROLE, SOCS_GRADUATE_ROLE]]
#     training_repository = TrainingRecordsRepository()
#
#     for role in graduate_roles:
#         log.info(f"[TRAINING] Attempting to populate Graduate role {role.name}.")
#         for member in role.members:
#             training_record = training_repository.get_or_create_training_record(member.id)
#
#             if training_record.jla_graduation_date is None and role.id == JLA_GRADUATE_ROLE:
#                 training_repository.set_graduation(member.id, JLA_GRADUATE_ROLE)
#             if training_record.snla_graduation_date is None and role.id == SNLA_GRADUATE_ROLE:
#                 training_repository.set_graduation(member.id, SNLA_GRADUATE_ROLE)
#             if training_record.ocs_graduation_date is None and role.id == OCS_GRADUATE_ROLE:
#                 training_repository.set_graduation(member.id, OCS_GRADUATE_ROLE)
#             if training_record.socs_graduation_date is None and role.id == SOCS_GRADUATE_ROLE:
#                 training_repository.set_graduation(member.id, SOCS_GRADUATE_ROLE)
#
#         log.info(f"[TRAINING] Finished populating Graduate role {role.name}.")
#
#     log.info("[TRAINING] Finished populating Graduate roles.")

async def process_training_record(message, channel):
    training_repository = TrainingRecordsRepository()
    omit_log_when_word = ["returned by:"]

    if channel.id == NRC_RECORDS_CHANNEL:
        for word in omit_log_when_word:
            if word.lower() in message.content.lower():
                log.info(f"[TRAINING] Skipping training record {message.id} as it contains the word '{word}'.")
                return

    training_repository.save_training(log_id=message.id, target_id=message.author.id, log_channel_id=channel.id,
                                      log_time=message.created_at)
    log.info(f"[TRAINING] Training record {message.id} processed.")
    training_repository.close_session()

async def populate_nrc_training_records(bot: commands.Bot, amount: int = 50):
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(NRC_RECORDS_CHANNEL)
    count = 0
    log.info(f"[TRAINING] Attempting to populate NRC training records from {channel.name}.")
    async for message in channel.history(limit=amount, oldest_first=False, after=TRAINING_POPULATE_FROM_DATE):

        try:
            await process_training_record(message, channel)
        except ValueError as e:
            log.warning(f"[TRAINING] Skipping training record {message.id} as it already exists.")
            continue

        count += 1
        log.info(f"[TRAINING] Processed NRC training record #{count}.")
        await asyncio.sleep(1)

    log.info("[TRAINING] Finished populating NRC training records.")

async def populate_netc_training_records(bot: commands.Bot, amount: int = 50):
    guild = bot.get_guild(NETC_GUILD_ID)
    channels = [channel_id for channel_id in NETC_RECORDS_CHANNELS]
    for channel in channels:
        channel = guild.get_channel(channel)
        count = 0
        log.info(f"[TRAINING] Attempting to populate NETC training records from {channel.name}.")
        async for message in channel.history(limit=amount, oldest_first=False, after=TRAINING_POPULATE_FROM_DATE):

            try:
                await process_training_record(message, channel)
            except ValueError as e:
                log.warning(f"[TRAINING] Skipping training record {message.id} as it already exists.")
                continue

            count += 1
            log.info(f"[TRAINING] Processed NETC training record from {channel.name} #{count}.")
            await asyncio.sleep(1)

        log.info(f"[TRAINING] Finished populating NETC training records from {channel.name}.")
    log.info("[TRAINING] Finished populating NETC training records.")