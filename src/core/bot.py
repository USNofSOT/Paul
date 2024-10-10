from __future__ import annotations

from typing import Optional
from discord.ext import commands
from logging import getLogger; log= getLogger("Bot")
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
        for fn in os.listdir('src/cogs'):
            if fn.endswith('.py'):
                await self.load_extension(f"cogs.{fn[:-3]}")
                await self.tree.sync() 
   