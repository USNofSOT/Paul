import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from src.cogs.commands.JE.check_awards import CheckAwards
from src.cogs.commands.NSC.briefing import (
    ShipBriefing,
    _EphemeralFollowup,
)
from src.security import Role


def test_briefing_is_a_group_with_clear_subcommands():
    assert ShipBriefing.__cog_group_name__ == "briefing"
    assert {command.name for command in ShipBriefing.__cog_app_commands__} == {
        "daily",
        "weekly",
    }

    for name in ("daily", "weekly"):
        command = next(
            command
            for command in ShipBriefing.__cog_app_commands__
            if command.name == name
        )
        assert [parameter.name for parameter in command.parameters] == ["ship"]
        assert command.checks[-1].__closure__[0].cell_contents == (Role.NSC_OBSERVER,)


def test_check_awards_is_an_active_je_command():
    command = CheckAwards.__cog_app_commands__[0]

    assert command.name == "check_awards"
    assert command.description == ("Check award eligibility for a member or role.")
    assert [parameter.name for parameter in command.parameters] == ["target"]
    assert command.checks[-1].__closure__[0].cell_contents == (Role.JE,)


def test_check_awards_sends_the_shared_briefing_embed():
    bot = MagicMock()
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = MagicMock(spec=discord.Guild)
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    target = MagicMock(spec=discord.Member)
    target.id = 1
    target.display_name = "Sailor"
    pending_award = MagicMock()
    embed = discord.Embed(title="Pending awards · Sailor")

    with (
        patch(
            "src.cogs.commands.JE.check_awards.ShipBriefingRepository"
        ) as repository_type,
        patch(
            "src.cogs.commands.JE.check_awards.get_pending_ship_awards",
            return_value=(pending_award,),
        ),
        patch(
            "src.cogs.commands.JE.check_awards.render_pending_award_embeds",
            return_value=(embed,),
        ) as render_embeds,
    ):
        repository = repository_type.return_value
        repository.get_sailors_by_ids.return_value = [MagicMock(discord_id=1)]
        repository.get_public_service_counts.return_value = {1: 3}
        callback = CheckAwards.check_awards.callback.__wrapped__
        asyncio.run(callback(CheckAwards(bot), interaction, target))

    render_embeds.assert_called_once_with(
        (pending_award,),
        subject_name="Sailor",
    )
    interaction.followup.send.assert_awaited_once()
    _, kwargs = interaction.followup.send.await_args
    assert kwargs["embeds"] == [embed]
    assert kwargs["ephemeral"] is True


def test_check_awards_does_not_report_all_clear_without_tracked_sailors():
    bot = MagicMock()
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = MagicMock(spec=discord.Guild)
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    target = MagicMock(spec=discord.Member)
    target.id = 1
    target.display_name = "Unknown Sailor"

    with patch(
        "src.cogs.commands.JE.check_awards.ShipBriefingRepository"
    ) as repository_type:
        repository_type.return_value.get_sailors_by_ids.return_value = []
        callback = CheckAwards.check_awards.callback.__wrapped__
        asyncio.run(callback(CheckAwards(bot), interaction, target))

    _, kwargs = interaction.followup.send.await_args
    assert "could not be evaluated" in kwargs["embeds"][0].description
    repository_type.return_value.get_public_service_counts.assert_not_called()


def test_manual_briefing_destination_is_always_ephemeral():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.followup.send = AsyncMock()
    destination = _EphemeralFollowup(interaction)

    asyncio.run(destination.send("Private briefing", embeds=[]))

    interaction.followup.send.assert_awaited_once_with(
        "Private briefing",
        embeds=[],
        ephemeral=True,
    )
