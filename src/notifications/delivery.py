from __future__ import annotations

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
            await channel.send(embed=EmbedNotificationRenderer.to_embed(rendered))
        except HTTPException:
            raise
