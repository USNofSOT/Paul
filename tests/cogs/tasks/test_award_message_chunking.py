import unittest

from src.cogs.tasks.task_check_awards import append_award_message_chunk
from src.cogs.tasks.task_check_representation_awards import (
    _build_pending_representation_header,
    _build_pending_representation_messages,
)
from src.data.models import RepresentationDepartment


class TestAwardMessageChunking(unittest.TestCase):
    def test_append_award_message_chunk_starts_new_message_when_limit_would_be_exceeded(self):
        # Arrange
        messages: list[str] = []

        # Act
        current_message = append_award_message_chunk(
            messages,
            current_message="abc",
            award_message="def",
            max_message_length=5,
        )

        # Assert
        self.assertEqual(messages, ["abc"])
        self.assertEqual(current_message, "def")

    def test_append_award_message_chunk_appends_when_message_fits(self):
        # Arrange
        messages: list[str] = []

        # Act
        current_message = append_award_message_chunk(
            messages,
            current_message="abc",
            award_message="de",
            max_message_length=5,
        )

        # Assert
        self.assertEqual(messages, [])
        self.assertEqual(current_message, "abcde")

    def test_pending_representation_messages_chunk_body_under_header(self):
        # Arrange
        header = _build_pending_representation_header(RepresentationDepartment.MEDIA)
        # Act
        messages = _build_pending_representation_messages(
            RepresentationDepartment.MEDIA,
            ["abc", "def"],
            max_message_length=len(header) + 5,
        )

        # Assert
        self.assertEqual(messages, [header + "abc", header + "def"])


if __name__ == "__main__":
    unittest.main()
