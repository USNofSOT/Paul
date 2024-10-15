from __future__ import annotations
import asyncio, discord, os, config
from logging import getLogger

from src.data import create_tables
from src.utils.logger import initialise_logger

log= getLogger(__name__)
from core import Bot

async def main():
    discord.utils.setup_logging()
    async with Bot() as bot:
        log.info("Attempting to start up bot")
        await bot.start(config.TOKEN, reconnect=True)

        @bot.event
        async def on_message(message):
            await bot.process_commands(message)  # Process commands here


if __name__ == '__main__':
    create_tables()
    initialise_logger()
    asyncio.run(main())