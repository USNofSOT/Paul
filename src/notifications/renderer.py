from __future__ import annotations

import discord

from src.notifications.types import NotificationPayload, RenderedNotification
from src.utils.embeds import default_embed


class EmbedNotificationRenderer:
    def render(self, payload: NotificationPayload) -> RenderedNotification:
        embed = default_embed(title=payload.title, description=payload.body, author=False)
        embed.color = self._resolve_color(payload)
        if payload.thumbnail_url:
            embed.set_thumbnail(url=payload.thumbnail_url)
        for field in payload.display_fields:
            embed.add_field(name=field.name, value=field.value, inline=field.inline)
        embed.set_footer(text=payload.footer)
        return RenderedNotification(
            embed_title=embed.title or "",
            embed_description=embed.description or "",
            fields=payload.display_fields,
            footer=payload.footer,
            color_value=embed.color.value,
            thumbnail_url=payload.thumbnail_url,
        )

    @staticmethod
    def to_embed(rendered: RenderedNotification) -> discord.Embed:
        embed = default_embed(
            title=rendered.embed_title,
            description=rendered.embed_description,
            author=False,
        )
        embed.color = discord.Color(rendered.color_value)
        if rendered.thumbnail_url:
            embed.set_thumbnail(url=rendered.thumbnail_url)
        if rendered.image_attachment_filename:
            embed.set_image(url=f"attachment://{rendered.image_attachment_filename}")
        for field in rendered.fields:
            embed.add_field(name=field.name, value=field.value, inline=field.inline)
        embed.set_footer(text=rendered.footer)
        return embed

    @staticmethod
    def _resolve_color(payload: NotificationPayload) -> discord.Color:
        if payload.days_remaining_label == "Due today" or "overdue" in payload.days_remaining_label:
            return discord.Color.red()
        if payload.template_key == "NO_HOSTING_REMINDER":
            return discord.Color.orange()
        return discord.Color.gold()
