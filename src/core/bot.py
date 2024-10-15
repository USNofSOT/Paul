from __future__ import annotations

from datetime import datetime
from logging import getLogger
from typing import Optional

from discord.ext import commands

from src.cogs import EXTENTIONS
from src.config import SPD_GUID_ID, ENGINE_ROOM

log= getLogger(__name__)
import discord

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
        embed = discord.Embed(
            title=":white_check_mark: Bot is now online",
            description="Bot is now online",
            color=discord.Color.green()
        )
        embed.set_footer(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            guild = self.get_guild(SPD_GUID_ID)
            channel = guild.get_channel(ENGINE_ROOM)
            await channel.send(embed=embed)
        except (AttributeError, discord.HTTPException, discord.NotFound):
            log.warning("Could not find the guild or channel for sending the online message")


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
        # await self.tree.sync()
        log.info("Tree Synced")

