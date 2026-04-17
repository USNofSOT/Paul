from __future__ import annotations

import asyncio
import os
import threading
from logging import getLogger

import discord
import uvicorn

from src.api.main import app as fastapi_app
from src.config.main_server import TOKEN
from src.core import Bot
from src.data import create_tables
from src.data.engine import engine_string
from src.data.migrations.migrate import run_migrations
from src.utils.logger import initialise_logger

log = getLogger(__name__)


def _run_api() -> None:
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        log_level="error",
    )


async def main():
    discord.utils.setup_logging()

    # Start the health check web server
    threading.Thread(target=_run_api, daemon=True, name="fastapi").start()

    async with Bot() as bot:
        log.info("Attempting to start up bot")
        await bot.start(TOKEN, reconnect=True)

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
