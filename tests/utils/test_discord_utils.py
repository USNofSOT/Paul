import unittest

from src.utils.discord_utils import (
    EngineerAlert,
    EngineerAlertField,
    DiscordEngineerAlertDispatcher,
    alert_engineers,
    send_engineer_alert,
    send_engineer_log,
)
from src.utils.embeds import AlertSeverity, engineer_alert_embed


class DummyChannel:
    def __init__(self, channel_id: int) -> None:
        self.id = channel_id
        self.sent_embeds = []

    async def send(self, embed=None):
        self.sent_embeds.append(embed)


class DummyEngineer:
    def __init__(self, member_id: int) -> None:
        self.id = member_id
        self.sent_embeds = []

    async def send(self, embed=None):
        self.sent_embeds.append(embed)


class DummyGuild:
    def __init__(self, members: dict[int, DummyEngineer], channels: dict[int, DummyChannel]):
        self.id = 1
        self._members = members
        self._channels = channels

    def get_member(self, member_id: int):
        return self._members.get(member_id)

    def get_channel(self, channel_id: int):
        return self._channels.get(channel_id)


class DummyBot:
    def __init__(self, guild: DummyGuild) -> None:
        self._guild = guild

    def get_guild(self, guild_id: int):
        del guild_id
        return self._guild


class TestDiscordUtils(unittest.IsolatedAsyncioTestCase):
    def test_engineer_alert_embed_uses_severity_label_and_fields(self) -> None:
        embed = engineer_alert_embed(
            severity=AlertSeverity.WARNING,
            title="Training Backfill Skipped",
            description="Skipped one missing channel.",
            fields=(("Channel ID", "`123`"),),
        )

        self.assertEqual(embed.title, "[WARNING] Training Backfill Skipped")
        self.assertEqual(embed.fields[0].name, "Channel ID")
        self.assertEqual(embed.fields[0].value, "`123`")

    async def test_send_engineer_log_posts_to_channel_without_dms(self) -> None:
        channel = DummyChannel(99)
        engineer = DummyEngineer(1)
        bot = DummyBot(DummyGuild({1: engineer}, {99: channel}))

        await send_engineer_log(
            bot,
            severity=AlertSeverity.INFO,
            title="Training Backfill Completed",
            description="Processed 24 NETC records.",
            fields=(EngineerAlertField("Count", "`24`"),),
            notify_engineers=False,
            channel_id=99,
            guild_id=1,
        )

        self.assertEqual(len(channel.sent_embeds), 1)
        self.assertEqual(channel.sent_embeds[0].title, "[INFO] Training Backfill Completed")
        self.assertEqual(len(engineer.sent_embeds), 0)

    async def test_alert_engineers_dms_engineers_with_structured_embed(self) -> None:
        engineer = DummyEngineer(42)
        bot = DummyBot(DummyGuild({42: engineer}, {}))
        dispatcher = DiscordEngineerAlertDispatcher()

        import src.utils.discord_utils as discord_utils_module

        original_engineers = discord_utils_module.ENGINEERS
        discord_utils_module.ENGINEERS = [42]
        try:
            await alert_engineers(
                bot,
                "Something failed.",
                RuntimeError("boom"),
                title="Command Task Failed",
                fields=(EngineerAlertField("Task", "`worker`"),),
                dispatcher=dispatcher,
            )
        finally:
            discord_utils_module.ENGINEERS = original_engineers

        self.assertEqual(len(engineer.sent_embeds), 1)
        self.assertEqual(engineer.sent_embeds[0].title, "[ERROR] Command Task Failed")

    async def test_dispatcher_posts_when_channel_matches_alert(self) -> None:
        channel = DummyChannel(55)
        bot = DummyBot(DummyGuild({}, {55: channel}))

        await send_engineer_alert(
            bot,
            EngineerAlert(
                severity=AlertSeverity.INFO,
                title="Scheduler Summary",
                description="No issues detected.",
                notify_engineers=False,
                guild_id=1,
                channel_id=55,
            ),
            dispatcher=DiscordEngineerAlertDispatcher(),
        )

        self.assertEqual(len(channel.sent_embeds), 1)
        self.assertEqual(channel.sent_embeds[0].title, "[INFO] Scheduler Summary")


if __name__ == "__main__":
    unittest.main()
