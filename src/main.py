from __future__ import annotations
import asyncio, discord, os, config
from core import Bot



async def main():
    discord.utils.setup_logging()
    async with Bot() as bot:
        await bot.start(config.TOKEN, reconnect=True)

        @bot.event
        async def on_message(message):
            await bot.process_commands(message)  # Process commands here

if __name__ == '__main__':
    asyncio.run(main())