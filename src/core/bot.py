from __future__ import annotations

from typing import Optional
from discord.ext import commands
from logging import getLogger

from discord.ext.commands import ExtensionNotFound, NoEntryPointError, ExtensionFailed

from src.cogs import EXTENTIONS

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
        log.info(f"Loading {len(EXTENTIONS)} extensions")
        for extension in EXTENTIONS:
            log.info(f"Loading {extension}")
            await self.load_extension(extension)
        log.info("All extentions loaded")
        await self.tree.sync()
        log.info("Tree Synced")

