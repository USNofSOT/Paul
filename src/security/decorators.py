import functools
import json
import logging
from typing import List, Set, Union

import discord
from discord import app_commands
from discord.ext import commands

from .evaluator import resolve_effective_roles
from .repository import SecurityInteractionRepository

log = logging.getLogger(__name__)


class InsufficientLevelError(app_commands.CheckFailure, commands.CheckFailure):
    """
    Exception raised when a user does not have the required roles to execute a command.
    Inherits from both app_commands and commands CheckFailure for compatibility.
    """

    def __init__(self, required_roles: List[str], possessed_roles: List[str]):
        self.required_roles = required_roles
        self.possessed_roles = possessed_roles
        super().__init__(f"User lacks required roles: {required_roles}")


def require_any_role(*roles: str):
    """
    Decorator to require that the user invoking the command has at least one
    of the specified roles. Works for both slash and text commands, as well
    as UI component interactions (buttons, selects).
    """

    def predicate(interaction_or_ctx: Union[discord.Interaction, commands.Context]) -> bool:
        user = interaction_or_ctx.user if isinstance(interaction_or_ctx,
                                                     discord.Interaction) else interaction_or_ctx.author
        user_roles: Set[str] = resolve_effective_roles(user)
        if any(role in user_roles for role in roles):
            return True
        raise InsufficientLevelError(list(roles), list(user_roles))

    def combined_check(func):
        if isinstance(func, app_commands.Command):
            # If it's already a command object, add the check to its list
            app_commands.check(predicate)(func)
            return func

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract interaction or context from args or kwargs
            interaction_or_ctx = None
            for arg in args:
                if isinstance(arg, (discord.Interaction, commands.Context)):
                    interaction_or_ctx = arg
                    break

            if not interaction_or_ctx:
                interaction_or_ctx = kwargs.get('interaction') or kwargs.get('ctx')

            if interaction_or_ctx:
                try:
                    predicate(interaction_or_ctx)
                except InsufficientLevelError as e:
                    # For UI interactions (buttons/selects) which aren't handled by command trees,
                    # we handle the error gracefully here.
                    if isinstance(interaction_or_ctx, discord.Interaction) and not interaction_or_ctx.command:
                        from .error_handler import handle_app_command_security_error
                        if await handle_app_command_security_error(interaction_or_ctx, e):
                            return
                    raise

            return await func(*args, **kwargs)

        # Apply both command and app_command checks to the wrapper
        # This ensures the checks are visible to the framework for /help, sync, etc.
        commands.check(predicate)(wrapper)
        app_commands.check(predicate)(wrapper)

        return wrapper

    return combined_check


def audit_interaction(func):
    """
    Decorator to log command executions (successes and failures) using
    the SecurityInteractionRepository. Works for both slash and text commands.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Determine context and user
        # For Cog methods, first arg is 'self'.
        # Second arg is interaction or ctx.

        interaction_or_ctx = None
        for arg in args:
            if isinstance(arg, (discord.Interaction, commands.Context)):
                interaction_or_ctx = arg
                break

        if not interaction_or_ctx:
            # Fallback to looking in kwargs
            interaction_or_ctx = kwargs.get('interaction') or kwargs.get('ctx')

        if not interaction_or_ctx:
            return await func(*args, **kwargs)

        user = interaction_or_ctx.user if isinstance(interaction_or_ctx,
                                                     discord.Interaction) else interaction_or_ctx.author

        if isinstance(interaction_or_ctx, discord.Interaction):
            command_name = interaction_or_ctx.command.qualified_name if interaction_or_ctx.command else func.__name__
        else:
            command_name = interaction_or_ctx.command.qualified_name if interaction_or_ctx.command else func.__name__

        # Capture kwargs for logging
        try:
            kwargs_json = json.dumps(kwargs, default=str)
        except (TypeError, ValueError):
            kwargs_json = str(kwargs)

        try:
            result = await func(*args, **kwargs)

            with SecurityInteractionRepository() as repository:
                repository.log_interaction(
                    discord_id=user.id,
                    command_name=command_name,
                    event_type="SUCCESS",
                    args=kwargs_json
                )
            return result
        except InsufficientLevelError:
            # Let the central error handler catch and log InsufficientLevelError
            raise
        except Exception as e:
            with SecurityInteractionRepository() as repository:
                repository.log_interaction(
                    discord_id=user.id,
                    command_name=command_name,
                    event_type="FAILURE",
                    details=str(e),
                    args=kwargs_json
                )
            raise

    return wrapper
