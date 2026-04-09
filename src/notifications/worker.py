from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from discord.ext import commands

from src.config.main_server import GUILD_ID
from src.config.notifications import (
    NOTIFICATION_DELIVERY_GRACE_HOURS,
    NOTIFICATION_MAX_DELIVERY_ATTEMPTS,
    NOTIFICATION_WORKER_BATCH_SIZE,
)
from src.data.repository.sailor_repository import SailorRepository
from src.notifications.admin.engineer_overview import build_ship_overview_field
from src.notifications.context import build_member_context
from src.notifications.contracts import (
    NotificationDeliveryAdapter,
    NotificationEligibilityEvaluator,
    NotificationEventRepositoryContract,
    NotificationRenderer,
    NotificationRouteResolver,
    TriggerDefinitionProvider,
)
from src.notifications.date_utils import ensure_utc
from src.notifications.payloads import NotificationPayloadFactory
from src.notifications.rollout import is_notification_enabled_for_member
from src.notifications.types import EligibilityResult, NotificationRunSummary
from src.utils.discord_utils import EngineerAlertField, alert_engineers

log = logging.getLogger(__name__)


class NotificationWorkerService:
    def __init__(
            self,
            definition_provider: TriggerDefinitionProvider,
            eligibility_evaluator: NotificationEligibilityEvaluator,
            route_resolver: NotificationRouteResolver,
            renderer: NotificationRenderer,
            delivery_adapter: NotificationDeliveryAdapter,
            event_repository: NotificationEventRepositoryContract,
            sailor_repository: SailorRepository,
            payload_factory: NotificationPayloadFactory,
            rollout_map,
    ) -> None:
        self.definition_provider = definition_provider
        self.eligibility_evaluator = eligibility_evaluator
        self.route_resolver = route_resolver
        self.renderer = renderer
        self.delivery_adapter = delivery_adapter
        self.event_repository = event_repository
        self.sailor_repository = sailor_repository
        self.payload_factory = payload_factory
        self.rollout_map = rollout_map

    async def run_once(
            self,
            bot: commands.Bot,
            reference_time: datetime | None = None,
            batch_size: int = NOTIFICATION_WORKER_BATCH_SIZE,
            grace_hours: int = NOTIFICATION_DELIVERY_GRACE_HOURS,
    ) -> NotificationRunSummary:
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            log.warning("Notification worker skipped because the guild is unavailable.")
            return NotificationRunSummary(event_count=0)

        delivered_count = 0
        resolved_now = ensure_utc(reference_time or datetime.now(UTC))
        delivery_deadline = resolved_now - timedelta(hours=grace_hours)
        pending_event_ids = self.event_repository.list_due_event_ids(
            limit=batch_size,
            due_before=resolved_now,
        )
        per_ship_counts: defaultdict[int | None, int] = defaultdict(int)
        cached_members = {
            member.id: member
            for member in getattr(guild, "members", [])
        }

        for event_id in pending_event_ids:
            if not self.event_repository.claim_event(event_id):
                continue

            event = self.event_repository.get_event(event_id)
            if event is None:
                continue

            scheduled_for_at = ensure_utc(event.scheduled_for_at)
            if scheduled_for_at < delivery_deadline:
                self.event_repository.mark_skipped(event_id, "delivery_window_elapsed")
                continue

            definition = self.definition_provider.get_definition(event.notification_type)
            sailor = self.sailor_repository.get_sailor(event.sailor_id)
            member = cached_members.get(event.sailor_id) or guild.get_member(
                event.sailor_id
            )
            if sailor is None or member is None:
                self.event_repository.mark_skipped(event_id, "sailor_or_member_missing")
                continue

            member_context = build_member_context(member)
            if not is_notification_enabled_for_member(
                    self.rollout_map,
                    definition.notification_type,
                    member_context,
            ):
                self.event_repository.mark_skipped(event_id, "rollout_disabled")
                continue

            if not self.eligibility_evaluator.matches_event(
                    definition,
                    sailor,
                    member_context,
                    event,
            ):
                self.event_repository.mark_skipped(event_id, "activity_cycle_changed")
                continue

            route = self.route_resolver.resolve(definition, member_context, guild)
            if route.destination_channel_id is None:
                self.event_repository.mark_skipped(
                    event_id,
                    route.skip_reason or "routing_unavailable",
                )
                continue

            payload = self.payload_factory.build(
                definition,
                sailor,
                member_context,
                self._event_to_eligibility(event),
                reference_time=resolved_now,
            )
            self.event_repository.update_payload_snapshot(
                event_id,
                self.payload_factory.to_snapshot(payload),
            )
            rendered = self.renderer.render(payload)
            try:
                await self.delivery_adapter.send(
                    guild,
                    route.destination_channel_id,
                    rendered,
                )
            except Exception as exc:
                next_attempt = int(event.attempt_count or 0) + 1
                if next_attempt >= NOTIFICATION_MAX_DELIVERY_ATTEMPTS:
                    final_attempt = self.event_repository.mark_failed(event_id, str(exc))
                    await alert_engineers(
                        bot,
                        (
                            f"Notification delivery exhausted retries for event {event_id} "
                            f"({event.notification_type}) sailor={event.sailor_id} "
                            f"ship_role={event.ship_role_id} attempts={final_attempt}"
                        ),
                        exception=exc,
                        title="Notification Delivery Failed",
                        fields=(
                            EngineerAlertField("Event ID", f"`{event_id}`"),
                            EngineerAlertField(
                                "Notification Type", f"`{event.notification_type}`"
                            ),
                            EngineerAlertField(
                                "Sailor ID", f"`{event.sailor_id}`"
                            ),
                            EngineerAlertField(
                                "Attempts", f"`{final_attempt}`"
                            ),
                            EngineerAlertField(
                                "Scheduled For",
                                f"<t:{int(scheduled_for_at.timestamp())}:f>",
                            ),
                            *tuple(
                                field
                                for field in (
                                    build_ship_overview_field({event.ship_role_id: 1}),
                                )
                                if field is not None
                            ),
                        ),
                    )
                else:
                    self.event_repository.release_for_retry(event_id, str(exc))
                continue

            self.event_repository.mark_delivered(event_id)
            delivered_count += 1
            per_ship_counts[event.ship_role_id] += 1

        return NotificationRunSummary(
            event_count=delivered_count,
            per_ship_counts=dict(per_ship_counts),
        )

    @staticmethod
    def _event_to_eligibility(event) -> EligibilityResult:
        return EligibilityResult(
            source_activity_at=ensure_utc(event.source_activity_at),
            source_activity_date=event.source_activity_date,
            threshold_at=ensure_utc(event.threshold_at),
            threshold_date=event.threshold_date,
            trigger_offset=event.trigger_offset,
            scheduled_for_at=ensure_utc(event.scheduled_for_at),
            scheduled_for_date=event.scheduled_for_date,
            days_remaining=(event.threshold_date - event.scheduled_for_date).days,
        )
