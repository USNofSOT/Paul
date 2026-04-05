import asyncio
from logging import getLogger
from typing import Any

from discord.ext import commands

from src.config.main_server import NRC_RECORDS_CHANNEL, GUILD_ID
from src.config.netc_server import NETC_GUILD_ID, ALL_NETC_RECORDS_CHANNELS
from src.config.spd_servers import SPD_GUILD_ID, ST_RECORDS_CHANNEL
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

def _get_channel_name(channel: Any) -> str:
    return getattr(channel, "name", f"channel-{getattr(channel, 'id', 'unknown')}")


async def _populate_training_records_from_channel(
        channel,
        *,
        amount: int | None,
        source_label: str,
) -> None:
    count = 0
    log.info(
        "[TRAINING] Attempting to populate %s training records from %s.",
        source_label,
        _get_channel_name(channel),
    )
    async for message in channel.history(
            limit=amount, oldest_first=False, after=TRAINING_POPULATE_FROM_DATE
    ):
        try:
            processed = await process_training_record(message, channel)
        except ValueError:
            log.warning(
                "[TRAINING] Skipping training record %s as it already exists.",
                getattr(message, "id", "unknown"),
            )
            continue
        except Exception as exc:
            log.exception(
                "[TRAINING] Failed to process %s training record %s from %s: %s",
                source_label,
                getattr(message, "id", "unknown"),
                _get_channel_name(channel),
                exc,
            )
            continue

        if not processed:
            continue

        count += 1
        log.info(
            "[TRAINING] Processed %s training record from %s #%s.",
            source_label,
            _get_channel_name(channel),
            count,
        )
        await asyncio.sleep(1)

    log.info(
        "[TRAINING] Finished populating %s training records from %s.",
        source_label,
        _get_channel_name(channel),
    )


async def process_training_record(message, channel) -> bool:
    training_repository = TrainingRecordsRepository()
    omit_log_when_word = ["returned by:"]
    try:
        channel_id = getattr(channel, "id", None)
        if channel_id is None:
            log.warning("[TRAINING] Skipping record because the target channel has no id.")
            return False

        author_id = getattr(getattr(message, "author", None), "id", None)
        if author_id is None:
            log.warning(
                "[TRAINING] Skipping training record %s in %s because the author id is missing.",
                getattr(message, "id", "unknown"),
                _get_channel_name(channel),
            )
            return False

        message_content = getattr(message, "content", "") or ""
        if channel_id == NRC_RECORDS_CHANNEL:
            for word in omit_log_when_word:
                if word.lower() in message_content.lower():
                    log.info(f"[TRAINING] Skipping training record {message.id} as it contains the word '{word}'.")
                    return False

        training_repository.save_training(
            log_id=message.id,
            target_id=author_id,
            log_channel_id=channel_id,
            log_time=getattr(message, "created_at", None),
        )
        log.info(f"[TRAINING] Training record {message.id} processed.")
        return True
    finally:
        training_repository.close_session()

async def populate_nrc_training_records(bot: commands.Bot, amount: int = 50):
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        log.warning("[TRAINING] Skipping NRC backfill because the main guild could not be resolved.")
        return

    channel = guild.get_channel(NRC_RECORDS_CHANNEL)
    if channel is None:
        log.warning("[TRAINING] Skipping NRC backfill because the records channel could not be resolved.")
        return

    await _populate_training_records_from_channel(
        channel,
        amount=amount,
        source_label="NRC",
    )

async def populate_st_training_records(bot: commands.Bot, amount: int = 50):
    guild = bot.get_guild(SPD_GUILD_ID)
    if guild is None:
        log.warning("[TRAINING] Skipping ST backfill because the SPD guild could not be resolved.")
        return

    channel = guild.get_channel(ST_RECORDS_CHANNEL)
    if channel is None:
        log.warning("[TRAINING] Skipping ST backfill because the records channel could not be resolved.")
        return

    await _populate_training_records_from_channel(
        channel,
        amount=amount,
        source_label="ST",
    )


async def populate_netc_training_records(bot: commands.Bot, amount: int = 50):
    guild = bot.get_guild(NETC_GUILD_ID)
    if guild is None:
        log.warning("[TRAINING] Skipping NETC backfill because the NETC guild could not be resolved.")
        return

    channel_ids = [channel_id for channel_id in ALL_NETC_RECORDS_CHANNELS]
    for channel_id in channel_ids:
        channel = guild.get_channel(channel_id)
        if channel is None:
            log.warning("[TRAINING] Skipping NETC backfill channel %s because it could not be resolved.", channel_id)
            continue
        await _populate_training_records_from_channel(
            channel,
            amount=amount,
            source_label="NETC",
        )
    log.info("[TRAINING] Finished populating NETC training records.")
