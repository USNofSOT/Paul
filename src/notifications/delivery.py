from __future__ import annotations

import io

import discord
from discord import Guild, HTTPException, TextChannel, Thread

from src.notifications.renderer import EmbedNotificationRenderer
from src.notifications.types import RenderedNotification


class DiscordNotificationDeliveryAdapter:
    async def send(
            self,
            guild: Guild,
            destination_channel_id: int,
            rendered: RenderedNotification,
    ) -> None:
        channel = guild.get_channel(destination_channel_id)
        if not isinstance(channel, TextChannel | Thread):
            raise LookupError(f"Channel {destination_channel_id} is not available.")

        try:
            embed = EmbedNotificationRenderer.to_embed(rendered)
            if rendered.image_attachment_bytes and rendered.image_attachment_filename:
                await channel.send(
                    embed=embed,
                    file=discord.File(
                        fp=io.BytesIO(rendered.image_attachment_bytes),
                        filename=rendered.image_attachment_filename,
                    ),
                )
            else:
                await channel.send(embed=embed)
        except HTTPException:
            raise
