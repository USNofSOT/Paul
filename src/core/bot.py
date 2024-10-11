from __future__ import annotations

from typing import Optional
from discord.ext import commands
from logging import getLogger

from discord.ext.commands import ExtensionNotFound, NoEntryPointError, ExtensionFailed

log= getLogger(__name__)
import discord, os


__all__ = (
    "Bot",
)

class Bot(discord.ext.commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
        )

    async def on_ready(self) -> None:
        log.info(f"logged in as {self.user}")


    async def success(self, content: str, interaction: discord.Interaction, ephemeral: Optional[bool]):
        """Sending success Message"""
        pass
    async def   error(self, content: str, interaction: discord.Interaction, ephemeral: Optional[bool]):
        """Sending error Message"""
        pass

    async def setup_hook(self):
        # Dynamically get all cogs in the cogs directory
        initial_extensions = [f"cogs.{filename[:-3]}" for filename in os.listdir("cogs") if filename.endswith(".py")]
        for extension in initial_extensions:
            try:
                log.info(f"Attempting to load extension: {extension}")
                await self.load_extension(extension)
            except Exception as e:
                log.error(f"Failed to load extension {extension}.", exc_info=e)
