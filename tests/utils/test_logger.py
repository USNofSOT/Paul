import logging

from src.utils.logger import NotifyEngineerHandler, NOTIFICATION_QUEUE


def test_notify_engineer_handler_queues_record():
    # Clear queue
    while not NOTIFICATION_QUEUE.empty():
        NOTIFICATION_QUEUE.get()

    handler = NotifyEngineerHandler()
    logger = logging.getLogger("test_notify")
    logger.addHandler(handler)

    # Test with flag
    logger.error("Test message", extra={"notify_engineer": True})
    assert NOTIFICATION_QUEUE.qsize() == 1
    record = NOTIFICATION_QUEUE.get()
    assert record.getMessage() == "Test message"

    # Test without flag
    logger.error("No notify message")
    assert NOTIFICATION_QUEUE.empty()
