from collections.abc import Sequence
from dataclasses import dataclass, field

import discord

MAX_EMBEDS_PER_MESSAGE = 10
MAX_EMBED_TEXT_PER_MESSAGE = 6_000


@dataclass(frozen=True)
class BriefingMessage:
    content: str | None = None
    embeds: tuple[discord.Embed, ...] = field(default_factory=tuple)
    files: tuple[discord.File, ...] = field(default_factory=tuple)
    allow_user_mentions: bool = False


def chunk_discord_embeds(
    embeds: Sequence[discord.Embed],
) -> tuple[tuple[discord.Embed, ...], ...]:
    """Split embeds on Discord's per-message count and text limits."""
    pages: list[tuple[discord.Embed, ...]] = []
    current: list[discord.Embed] = []
    current_text_length = 0

    for embed in embeds:
        embed_text_length = len(embed)
        exceeds_count = len(current) >= MAX_EMBEDS_PER_MESSAGE
        exceeds_text = (
            bool(current)
            and current_text_length + embed_text_length > MAX_EMBED_TEXT_PER_MESSAGE
        )
        if exceeds_count or exceeds_text:
            pages.append(tuple(current))
            current = []
            current_text_length = 0

        current.append(embed)
        current_text_length += embed_text_length

    if current:
        pages.append(tuple(current))
    return tuple(pages)
