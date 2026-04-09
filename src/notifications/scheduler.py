from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from discord.ext import commands

from src.config.main_server import GUILD_ID
from src.config.notifications import (
    NOTIFICATION_LOOKAHEAD_HOURS,
    NOTIFICATION_ROLLOUT,
    NotificationRolloutMap,
)
from src.data.repository.sailor_repository import SailorRepository
from src.notifications.context import build_member_context
from src.notifications.contracts import (
    NotificationEligibilityEvaluator,
    NotificationEventRepositoryContract,
    NotificationRouteResolver,
    TriggerDefinitionProvider,
)
from src.notifications.date_utils import ensure_utc
from src.notifications.payloads import NotificationPayloadFactory
from src.notifications.rollout import is_notification_enabled_for_member
from src.notifications.types import NotificationRunSummary

log = logging.getLogger(__name__)


class NotificationSchedulerService:
    def __init__(
            self,
            definition_provider: TriggerDefinitionProvider,
            eligibility_evaluator: NotificationEligibilityEvaluator,
            route_resolver: NotificationRouteResolver,
            event_repository: NotificationEventRepositoryContract,
            sailor_repository: SailorRepository,
            payload_factory: NotificationPayloadFactory,
            rollout_map: NotificationRolloutMap | None = None,
    ) -> None:
        self.definition_provider = definition_provider
        self.eligibility_evaluator = eligibility_evaluator
        self.route_resolver = route_resolver
        self.event_repository = event_repository
        self.sailor_repository = sailor_repository
        self.payload_factory = payload_factory
        self.rollout_map = rollout_map if rollout_map is not None else NOTIFICATION_ROLLOUT

    async def run_once(
            self,
            bot: commands.Bot,
            reference_time: datetime | None = None,
            lookahead_hours: int = NOTIFICATION_LOOKAHEAD_HOURS,
    ) -> NotificationRunSummary:
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            log.warning("Notification scheduler skipped because the guild is unavailable.")
            return NotificationRunSummary(event_count=0)

        resolved_now = ensure_utc(reference_time or datetime.now(UTC))
        resolved_window_start = resolved_now
        resolved_window_end = resolved_window_start + timedelta(hours=lookahead_hours)
        created_events = 0
        per_ship_counts: defaultdict[int | None, int] = defaultdict(int)
        cached_members = {
            member.id: member
            for member in getattr(guild, "members", [])
        }

        definitions = self.definition_provider.get_definitions()
        activity_fields = list({d.activity_field for d in definitions})
        sailors = self.sailor_repository.get_sailors_with_any_activity(activity_fields)

        for sailor in sailors:
            member = cached_members.get(sailor.discord_id) or guild.get_member(
                sailor.discord_id
            )
            if member is None:
                continue

            member_context = build_member_context(member)

            for definition in definitions:
                if not is_notification_enabled_for_member(
                        self.rollout_map,
                        definition.notification_type,
                        member_context,
                ):
                    continue

                projected_eligibilities = self.eligibility_evaluator.project_for_window(
                    definition,
                    sailor,
                    member_context,
                    resolved_window_start,
                    resolved_window_end,
                )
                if not projected_eligibilities:
                    continue

                route = self.route_resolver.resolve(definition, member_context, guild)

                for eligibility in projected_eligibilities:
                    payload = self.payload_factory.build(
                        definition,
                        sailor,
                        member_context,
                        eligibility,
                        reference_time=resolved_now,
                    )
                    payload_snapshot = self.payload_factory.to_snapshot(payload)
                    if route.destination_channel_id is None:
                        _, created = self.event_repository.create_skipped_event(
                            definition=definition,
                            sailor=sailor,
                            member_context=member_context,
                            eligibility=eligibility,
                            payload_snapshot=payload_snapshot,
                            skip_reason=route.skip_reason or "routing_unavailable",
                        )
                    else:
                        _, created = self.event_repository.create_pending_event(
                            definition=definition,
                            sailor=sailor,
                            member_context=member_context,
                            eligibility=eligibility,
                            destination_channel_id=route.destination_channel_id,
                            payload_snapshot=payload_snapshot,
                        )
                    if created:
                        created_events += 1
                        per_ship_counts[member_context.ship_role_id] += 1

        return NotificationRunSummary(
            event_count=created_events,
            per_ship_counts=dict(per_ship_counts),
        )
