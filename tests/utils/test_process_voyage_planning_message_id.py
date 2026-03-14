from src.utils import process_voyage_log


def configure_parser(guild_id, voyage_planning, voyage_announcements):
    process_voyage_log.GUILD_ID = guild_id
    process_voyage_log.VOYAGE_PLANNING = voyage_planning
    process_voyage_log.VOYAGE_ANNOUNCEMENTS = voyage_announcements


def assert_reference_matches(content, expected_reference, expected_message_id):
    assert (
            process_voyage_log.get_voyage_planning_message_reference_from_content(content)
            == expected_reference
    )
    assert (
            process_voyage_log.get_voyage_planning_message_id_from_content(content)
            == expected_message_id
    )


def test_parses_discord_com_voyage_planning_link():
    configure_parser(111111, 22222, 33333)
    assert_reference_matches(
        "https://discord.com/channels/111111/22222/987654321",
        (22222, 987654321),
        987654321,
    )


def test_parses_discordapp_com_voyage_planning_link():
    configure_parser("1", "2", "3")
    assert_reference_matches(
        "https://discordapp.com/channels/1/2/123",
        (2, 123),
        123,
    )


def test_parses_prefixed_voyage_planning_link():
    configure_parser(999999, 88888, 77777)
    assert_reference_matches(
        "VP: https://discord.com/channels/999999/88888/55555",
        (88888, 55555),
        55555,
    )


def test_parses_voyage_announcement_link():
    configure_parser(123456, 65432, 76543)
    assert_reference_matches(
        "https://discord.com/channels/123456/76543/13579",
        (76543, 13579),
        13579,
    )


def test_parses_second_discordapp_com_voyage_planning_link():
    configure_parser(3, 4, 5)
    assert_reference_matches(
        "https://discordapp.com/channels/3/4/321",
        (4, 321),
        321,
    )


def test_rejects_link_when_reference_is_not_at_end():
    configure_parser(777777, 66666, 55555)
    content = "https://discord.com/channels/777777/66666/44444 VP"
    assert_reference_matches(content, None, None)
