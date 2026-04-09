from __future__ import annotations

import asyncio
from logging import getLogger

import discord

import config
from core import Bot
from data.engine import engine_string
from data.migrations.migrate import run_migrations
from src.data import create_tables
from src.utils.logger import initialise_logger

log = getLogger(__name__)


async def main():
    discord.utils.setup_logging()
    async with Bot() as bot:
        log.info("Attempting to start up bot")
        await bot.start(config.TOKEN, reconnect=True)

        @bot.event
        async def on_message(message):
            await bot.process_commands(message)  # Process commands here


if __name__ == "__main__":
    initialise_logger()
    log.info("Initialising database tables")
    create_tables()
    log.info("Running database migrations")
    run_migrations(engine_string)
    log.info("Startup bootstrap complete; launching bot event loop")
    asyncio.run(main())
