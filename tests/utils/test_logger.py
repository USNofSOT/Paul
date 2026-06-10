import logging
from unittest.mock import MagicMock

from src.utils.logger import NotifyEngineerHandler, set_notification_callback


def test_notify_engineer_handler_calls_callback():
    # Arrange
    callback = MagicMock()
    set_notification_callback(callback)

    handler = NotifyEngineerHandler()
    logger = logging.getLogger("test_notify")
    logger.addHandler(handler)
    logger.propagate = False  # Prevent logs from leaking to console during test

    try:
        # Act
        logger.error("Test message", extra={"notify_engineer": True})

        # Assert
        assert callback.called
        record = callback.call_args[0][0]
        assert record.getMessage() == "Test message"

        # Arrange
        callback.reset_mock()

        # Act
        logger.error("No notify message")
        # Assert
        assert not callback.called
    finally:
        # Cleanup
        set_notification_callback(None)
        logger.removeHandler(handler)
