from __future__ import annotations

from src.config.notifications import NOTIFICATION_ROLLOUT, NotificationRolloutMap
from src.data.repository.notification_event_repository import NotificationEventRepository
from src.data.repository.sailor_repository import SailorRepository
from src.notifications.definitions import DefaultTriggerDefinitionProvider
from src.notifications.delivery import DiscordNotificationDeliveryAdapter
from src.notifications.evaluator import SailorInactivityEligibilityEvaluator
from src.notifications.payloads import NotificationPayloadFactory
from src.notifications.renderer import EmbedNotificationRenderer
from src.notifications.routing import ShipCommandRouteResolver
from src.notifications.scheduler import NotificationSchedulerService
from src.notifications.worker import NotificationWorkerService


class NotificationServiceFactory:
    def __init__(
            self,
            *,
            rollout_map: NotificationRolloutMap | None = None,
    ) -> None:
        self.rollout_map = rollout_map if rollout_map is not None else NOTIFICATION_ROLLOUT

    @staticmethod
    def build_definition_provider() -> DefaultTriggerDefinitionProvider:
        return DefaultTriggerDefinitionProvider()

    @staticmethod
    def build_payload_factory() -> NotificationPayloadFactory:
        return NotificationPayloadFactory()

    @staticmethod
    def build_route_resolver() -> ShipCommandRouteResolver:
        return ShipCommandRouteResolver()

    @staticmethod
    def build_eligibility_evaluator() -> SailorInactivityEligibilityEvaluator:
        return SailorInactivityEligibilityEvaluator()

    @staticmethod
    def build_renderer() -> EmbedNotificationRenderer:
        return EmbedNotificationRenderer()

    @staticmethod
    def build_delivery_adapter() -> DiscordNotificationDeliveryAdapter:
        return DiscordNotificationDeliveryAdapter()

    def build_scheduler(
            self,
            *,
            event_repository: NotificationEventRepository,
            sailor_repository: SailorRepository,
    ) -> NotificationSchedulerService:
        return NotificationSchedulerService(
            definition_provider=self.build_definition_provider(),
            eligibility_evaluator=self.build_eligibility_evaluator(),
            route_resolver=self.build_route_resolver(),
            event_repository=event_repository,
            sailor_repository=sailor_repository,
            payload_factory=self.build_payload_factory(),
            rollout_map=self.rollout_map,
        )

    def build_worker(
            self,
            *,
            event_repository: NotificationEventRepository,
            sailor_repository: SailorRepository,
    ) -> NotificationWorkerService:
        return NotificationWorkerService(
            definition_provider=self.build_definition_provider(),
            eligibility_evaluator=self.build_eligibility_evaluator(),
            route_resolver=self.build_route_resolver(),
            renderer=self.build_renderer(),
            delivery_adapter=self.build_delivery_adapter(),
            event_repository=event_repository,
            sailor_repository=sailor_repository,
            payload_factory=self.build_payload_factory(),
            rollout_map=self.rollout_map,
        )
