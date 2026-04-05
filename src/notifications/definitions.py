from __future__ import annotations

from src.config.notifications import (
    NOTIFICATION_DEFINITION_CONFIGS,
    NotificationDefinitionConfigMap,
)
from src.notifications.types import (
    NotificationDefinition,
    NotificationType,
)


class DefaultTriggerDefinitionProvider:
    def __init__(
            self,
            definition_configs: NotificationDefinitionConfigMap | None = None,
    ) -> None:
        resolved_configs = (
            definition_configs
            if definition_configs is not None
            else NOTIFICATION_DEFINITION_CONFIGS
        )
        self._definitions = tuple(
            NotificationDefinition(
                notification_type=notification_type,
                activity_field=config.activity_field,
                threshold_days=config.threshold_days,
                trigger_offsets=config.trigger_offsets,
                template_key=config.template_key,
                routing_target=config.routing_target,
            )
            for notification_type, config in resolved_configs.items()
        )
        self._definitions_by_type = {
            definition.notification_type.value: definition for definition in self._definitions
        }

    def get_definitions(self) -> tuple[NotificationDefinition, ...]:
        return self._definitions

    def get_definition(
            self,
            notification_type: str | NotificationType,
    ) -> NotificationDefinition:
        key = (
            notification_type.value
            if isinstance(notification_type, NotificationType)
            else notification_type
        )
        return self._definitions_by_type[key]
