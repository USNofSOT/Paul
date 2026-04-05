import unittest

from src.notifications.service_factory import NotificationServiceFactory


class TestNotificationServiceFactory(unittest.TestCase):
    def test_factory_reuses_shared_components(self) -> None:
        factory = NotificationServiceFactory()

        self.assertIs(
            factory.build_definition_provider(),
            factory.build_definition_provider(),
        )
        self.assertIs(
            factory.build_payload_factory(),
            factory.build_payload_factory(),
        )
        self.assertIs(
            factory.build_renderer(),
            factory.build_renderer(),
        )
        self.assertIs(
            factory.build_delivery_adapter(),
            factory.build_delivery_adapter(),
        )
