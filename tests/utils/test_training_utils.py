import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils import training_utils as training_utils_module
from src.utils.training_utils import (
    populate_netc_training_records,
    process_training_record,
)


class DummyChannel:
    def __init__(self, channel_id: int, name: str, messages=None) -> None:
        self.id = channel_id
        self.name = name
        self._messages = list(messages or [])

    def history(self, limit=None, oldest_first=False, after=None):
        del limit, oldest_first, after

        async def generator():
            for message in self._messages:
                yield message

        return generator()


class DummyGuild:
    def __init__(self, channels: dict[int, DummyChannel | None]) -> None:
        self._channels = channels

    def get_channel(self, channel_id: int):
        return self._channels.get(channel_id)


class DummyBot:
    def __init__(self, guild) -> None:
        self._guild = guild

    def get_guild(self, guild_id: int):
        del guild_id
        return self._guild


class TestTrainingUtils(unittest.IsolatedAsyncioTestCase):
    async def test_process_training_record_skips_messages_without_author_id(self) -> None:
        repository = MagicMock()
        message = SimpleNamespace(
            id=123,
            author=SimpleNamespace(id=None),
            content="Completed training",
            created_at=datetime(2026, 4, 5, tzinfo=UTC),
        )
        channel = DummyChannel(456, "netc-records")

        with patch(
                "src.utils.training_utils.TrainingRecordsRepository",
                return_value=repository,
        ):
            processed = await process_training_record(message, channel)

        self.assertFalse(processed)
        repository.save_training.assert_not_called()
        repository.close_session.assert_called_once()

    async def test_populate_netc_training_records_skips_missing_channels(self) -> None:
        resolved_channel = DummyChannel(2, "resolved-records")
        bot = DummyBot(DummyGuild({1: None, 2: resolved_channel}))

        with patch.object(training_utils_module, "ALL_NETC_RECORDS_CHANNELS", (1, 2)):
            await populate_netc_training_records(bot, amount=10)

        self.assertEqual(resolved_channel.name, "resolved-records")

    async def test_populate_netc_training_records_continues_after_record_error(self) -> None:
        channel = DummyChannel(
            2,
            "resolved-records",
            messages=[
                SimpleNamespace(id=1),
                SimpleNamespace(id=2),
            ],
        )
        bot = DummyBot(DummyGuild({2: channel}))

        with patch.object(training_utils_module, "ALL_NETC_RECORDS_CHANNELS", (2,)):
            with patch(
                    "src.utils.training_utils.process_training_record",
                    new=AsyncMock(side_effect=[RuntimeError("boom"), True]),
            ) as process_mock:
                await populate_netc_training_records(bot, amount=10)

        self.assertEqual(process_mock.await_count, 2)


if __name__ == "__main__":
    unittest.main()
