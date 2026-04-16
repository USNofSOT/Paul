import asyncio
import logging
import unittest
from unittest.mock import patch

from src.utils.embeds import AlertSeverity
from src.utils.logger import PaulLogger, register_bot


class DummyBot:
    pass


class TestPaulLogger(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = DummyBot()
        register_bot(self.bot)
        self.logger = logging.getLogger("test_paul_logger")

    def test_logger_is_paul_logger(self):
        self.assertIsInstance(self.logger, PaulLogger)

    @patch("src.utils.discord_utils.send_engineer_log")
    async def test_error_with_notify_engineer(self, mock_send_log):
        # We need a running loop for create_task
        mock_send_log.return_value = asyncio.Future()
        mock_send_log.return_value.set_result(None)

        with self.assertLogs("test_paul_logger", level="ERROR") as cm:
            self.logger.error("Test error message", notify_engineer=True)

        # Give it a tiny bit of time for the task to be created and mock to be called
        await asyncio.sleep(0.1)

        self.assertEqual(cm.output, ["ERROR:test_paul_logger:Test error message"])
        mock_send_log.assert_called_once()
        args, kwargs = mock_send_log.call_args
        self.assertEqual(kwargs["severity"], AlertSeverity.ERROR)
        self.assertEqual(kwargs["description"], "Test error message")
        self.assertTrue(kwargs["notify_engineers"])

    @patch("src.utils.discord_utils.send_engineer_log")
    async def test_warning_with_notify_engineer(self, mock_send_log):
        mock_send_log.return_value = asyncio.Future()
        mock_send_log.return_value.set_result(None)

        with self.assertLogs("test_paul_logger", level="WARNING") as cm:
            self.logger.warning("Test warning message", notify_engineer=True)

        await asyncio.sleep(0.1)

        self.assertEqual(cm.output, ["WARNING:test_paul_logger:Test warning message"])
        mock_send_log.assert_called_once()
        self.assertEqual(mock_send_log.call_args[1]["severity"], AlertSeverity.WARNING)

    @patch("src.utils.discord_utils.send_engineer_log")
    async def test_error_without_notify_engineer(self, mock_send_log):
        with self.assertLogs("test_paul_logger", level="ERROR") as cm:
            self.logger.error("Test error no notify")

        await asyncio.sleep(0.1)

        self.assertEqual(cm.output, ["ERROR:test_paul_logger:Test error no notify"])
        mock_send_log.assert_not_called()

    @patch("src.utils.discord_utils.send_engineer_log")
    async def test_error_with_args_formatting(self, mock_send_log):
        mock_send_log.return_value = asyncio.Future()
        mock_send_log.return_value.set_result(None)

        self.logger.error("Error %d: %s", 500, "Internal Server Error", notify_engineer=True)

        await asyncio.sleep(0.1)

        mock_send_log.assert_called_once()
        self.assertEqual(mock_send_log.call_args[1]["description"], "Error 500: Internal Server Error")


if __name__ == "__main__":
    unittest.main()
