from __future__ import annotations

import sys
import types

from discord import app_commands
from discord.ext import commands

from src.config.cooldowns import command_cooldown as commands_cooldown_spec
from src.core.command_cooldowns import (
    COOLDOWN_SECONDS_KEY,
    COOLDOWN_TRACKING_KEY,
    apply_configured_cooldowns,
    build_cooldown_error_embed,
    build_cooldown_stats_payload,
    record_command_cooldown_event,
)


class _FakeTree:
    def __init__(self, app_command_items: list[app_commands.Command]):
        self._app_command_items = app_command_items

    def walk_commands(self):
        return list(self._app_command_items)


class _FakeBot:
    def __init__(
            self,
            app_command_items: list[app_commands.Command],
            text_commands: list[commands.Command],
    ):
        self.tree = _FakeTree(app_command_items)
        self._text_commands = text_commands

    def walk_commands(self):
        return list(self._text_commands)


async def _slash_callback(interaction):
    del interaction


@commands.command(name="futurecommand")
async def _text_callback(ctx):
    del ctx


def test_apply_configured_cooldowns_tracks_message_and_skips_zero_second_items():
    ships_command = app_commands.Command(
        name="ships",
        description="Ship report",
        callback=_slash_callback,
    )
    future_command = _text_callback
    baseline_ship_checks = len(ships_command.checks)

    apply_configured_cooldowns(
        _FakeBot([ships_command], [future_command]),
    )

    assert ships_command.extras[COOLDOWN_SECONDS_KEY] == 20
    assert COOLDOWN_TRACKING_KEY in ships_command.extras
    assert len(ships_command.checks) == baseline_ship_checks + 1

    assert future_command.extras[COOLDOWN_SECONDS_KEY] == 0
    assert COOLDOWN_TRACKING_KEY in future_command.extras


def test_build_cooldown_error_embed_uses_configured_message_template():
    embed = build_cooldown_error_embed("ships", 12.1)

    assert embed.title == "Command on cooldown"
    assert embed.description == (
        "Please wait 13 seconds before using `ships` again."
    )


def test_record_command_cooldown_event_tracks_rendered_message(monkeypatch):
    recorded_calls = []

    class _FakeRepository:
        def record_cooldown(self, command_name, **kwargs):
            recorded_calls.append((command_name, kwargs))

        def close_session(self):
            return None

    fake_module = types.ModuleType(
        "src.data.repository.command_cooldown_stats_repository"
    )
    fake_module.CommandCooldownStatsRepository = _FakeRepository
    monkeypatch.setitem(
        sys.modules,
        "src.data.repository.command_cooldown_stats_repository",
        fake_module,
    )

    rendered_message = record_command_cooldown_event("Ships", 12.1)

    assert rendered_message == (
        "Please wait 13 seconds before using `ships` again."
    )
    assert recorded_calls == [
        (
            "ships",
            {
                "cooldown_seconds": 20,
                "retry_after_seconds": 13,
            },
        )
    ]


def test_build_cooldown_stats_payload_sanitizes_names_and_mentions():
    payload = build_cooldown_stats_payload(
        "Weird\nCommand <@123>",
        4.2,
        spec=commands_cooldown_spec(
            7,
            "Slow down <@123> before using {command_name} again.",
        ),
    )

    assert payload["command_name"] == "weird_command _123_"
    assert payload["cooldown_seconds"] == 7
    assert payload["retry_after_seconds"] == 5
    assert payload["rendered_message"] == (
        "Slow down <@\u200b123> before using weird_command _123_ again."
    )
