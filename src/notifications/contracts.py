from __future__ import annotations

from datetime import datetime
from typing import Protocol

from discord import Guild

from src.data.models import NotificationEvent, Sailor
from src.notifications.types import (
    EligibilityResult,
    NotificationDefinition,
    NotificationPayload,
    RenderedNotification,
    ResolvedMemberContext,
    ResolvedRoute,
    ShipHealthSummary,
    ShipHealthSummaryRunSummary,
)


class TriggerDefinitionProvider(Protocol):
    def get_definitions(self) -> tuple[NotificationDefinition, ...]: ...

    def get_definition(self, notification_type: str) -> NotificationDefinition: ...


class NotificationEligibilityEvaluator(Protocol):
    def project_for_window(
            self,
            definition: NotificationDefinition,
            sailor: Sailor,
            member_context: ResolvedMemberContext,
            window_start: datetime,
            window_end: datetime,
    ) -> tuple[EligibilityResult, ...]: ...

    def matches_event(
            self,
            definition: NotificationDefinition,
            sailor: Sailor,
            member_context: ResolvedMemberContext,
            event: NotificationEvent,
    ) -> bool: ...


class NotificationEventRepositoryContract(Protocol):
    def create_pending_event(
            self,
            *,
            definition: NotificationDefinition,
            sailor: Sailor,
            member_context: ResolvedMemberContext,
            eligibility: EligibilityResult,
            destination_channel_id: int | None,
            payload_snapshot: str,
    ) -> tuple[NotificationEvent, bool]: ...

    def create_skipped_event(
            self,
            *,
            definition: NotificationDefinition,
            sailor: Sailor,
            member_context: ResolvedMemberContext,
            eligibility: EligibilityResult,
            payload_snapshot: str,
            skip_reason: str,
    ) -> tuple[NotificationEvent, bool]: ...

    def list_due_event_ids(self, *, limit: int, due_before: datetime) -> list[int]: ...

    def claim_event(self, event_id: int) -> bool: ...

    def get_event(self, event_id: int) -> NotificationEvent | None: ...

    def list_recent_events(self, *, limit: int = 10) -> list[NotificationEvent]: ...

    def count_by_status(self) -> dict[str, int]: ...

    def update_payload_snapshot(self, event_id: int, payload_snapshot: str) -> None: ...

    def mark_delivered(self, event_id: int) -> None: ...

    def mark_skipped(self, event_id: int, reason: str) -> None: ...

    def release_for_retry(self, event_id: int, reason: str) -> int: ...

    def mark_failed(self, event_id: int, reason: str) -> int: ...


class NotificationRouteResolver(Protocol):
    def resolve_ship_role(
            self,
            ship_role_id: int | None,
            guild: Guild,
    ) -> ResolvedRoute: ...

    def resolve(
            self,
            definition: NotificationDefinition,
            member_context: ResolvedMemberContext,
            guild: Guild,
    ) -> ResolvedRoute: ...


class NotificationRenderer(Protocol):
    def render(self, payload: NotificationPayload) -> RenderedNotification: ...


class NotificationDeliveryAdapter(Protocol):
    async def send(
            self,
            guild: Guild,
            destination_channel_id: int,
            rendered: RenderedNotification,
    ) -> None: ...


class ShipHealthSummaryDataProvider(Protocol):
    def build_summary(
            self,
            *,
            ship_role_id: int,
            ship_name: str,
            ship_size: int,
            sailor_ids: list[int],
            reference_time: datetime,
    ) -> ShipHealthSummary: ...


class ShipHealthSummaryRenderer(Protocol):
    def render(self, summary: ShipHealthSummary) -> RenderedNotification: ...


class ShipHealthSummaryServiceContract(Protocol):
    async def run_once(
            self,
            bot,
            reference_time: datetime | None = None,
    ) -> ShipHealthSummaryRunSummary: ...
