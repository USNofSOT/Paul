import logging
from unittest.mock import MagicMock

from src.utils.logger import NotifyEngineerHandler, set_notification_callback


def test_notify_engineer_handler_calls_callback():
    # Setup mock callback
    callback = MagicMock()
    set_notification_callback(callback)

    handler = NotifyEngineerHandler()
    logger = logging.getLogger("test_notify")
    logger.addHandler(handler)
    logger.propagate = False  # Prevent logs from leaking to console during test

    try:
        # Test with flag
        logger.error("Test message", extra={"notify_engineer": True})

        assert callback.called
        record = callback.call_args[0][0]
        assert record.getMessage() == "Test message"

        # Reset mock
        callback.reset_mock()

        # Test without flag
        logger.error("No notify message")
        assert not callback.called
    finally:
        # Cleanup
        set_notification_callback(None)
        logger.removeHandler(handler)
