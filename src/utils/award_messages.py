from unittest.mock import AsyncMock, MagicMock

import discord
from discord.ext import commands
from discord.ext.commands.view import StringView

from src.config import MAX_MESSAGE_LENGTH
from src.utils.check_awards import check_sailor


def fake_context(bot, guild, channel_name: str = "test-channel"):
    message = MagicMock(spec=discord.Message)
    message.author = MagicMock(spec=discord.User)
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.name = channel_name
    context = commands.Context(
        bot=bot,
        message=message,
        view=StringView(buffer=""),
    )
    context.guild.name = "USN"
    context.guild.roles = None
    context.guild.members = None
    context.guild.get_member = None
    context.send = AsyncMock()
    return context


def append_award_message_chunk(
    messages: list[str],
    current_message: str,
    award_message: str,
    max_message_length: int = MAX_MESSAGE_LENGTH,
) -> str:
    if len(current_message + award_message) <= max_message_length:
        return current_message + award_message
    if current_message:
        messages.append(current_message)
    return award_message


def create_award_messages(
    role,
    sailor_repository,
    guild,
    context,
    *,
    exclude_roles: tuple[discord.Role, ...] = (),
) -> list[str]:
    messages: list[str] = []
    current_message = ""
    for member in role.members:
        if any(excluded in member.roles for excluded in exclude_roles):
            continue
        sailor = sailor_repository.get_sailor(member.id)
        if sailor is None:
            continue
        for award_message in check_sailor(guild, context, sailor, member):
            current_message = append_award_message_chunk(
                messages,
                current_message,
                award_message,
            )
    if current_message:
        messages.append(current_message)
    return messages
