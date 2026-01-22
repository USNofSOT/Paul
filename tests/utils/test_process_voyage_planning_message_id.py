import pytest

from src.utils import process_voyage_log


@pytest.mark.parametrize(
    "guild_id,voyage_planning,content,expected",
    [
        (111111, 22222, "https://discord.com/channels/111111/22222/987654321", 987654321),
        ("1", "2", "https://discordapp.com/channels/1/2/123", 123),
        (999999, 88888, "VP: https://discord.com/channels/999999/88888/55555", 55555),
        (123456, 65432, "https://discord.com/channels/123456/65432/0", 0),
        (777777, 66666, "https://discord.com/channels/777777/66666/44444 VP", None),
    ],
)
def test_get_voyage_planning_message_id_matches(guild_id, voyage_planning, content, expected):
    process_voyage_log.GUILD_ID = guild_id
    process_voyage_log.VOYAGE_PLANNING = voyage_planning
    assert process_voyage_log.get_voyage_planning_message_id_from_content(content) == expected


def test_no_match_returns_none():
    process_voyage_log.GUILD_ID = 1
    process_voyage_log.VOYAGE_PLANNING = 2
    assert process_voyage_log.get_voyage_planning_message_id_from_content(
        "this message contains no discord link") is None


def test_link_not_at_end_returns_none():
    process_voyage_log.GUILD_ID = 1
    process_voyage_log.VOYAGE_PLANNING = 2
    content = f"https://discord.com/channels/{process_voyage_log.GUILD_ID}/{process_voyage_log.VOYAGE_PLANNING}/123 extra"
    assert process_voyage_log.get_voyage_planning_message_id_from_content(content) is None
