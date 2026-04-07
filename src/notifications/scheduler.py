from __future__ import annotations

import logging
from datetime import date

from discord.ext import commands

from src.config.main_server import GUILD_ID
from src.config.notifications import NOTIFICATION_ROLLOUT, NotificationRolloutMap
from src.data.repository.sailor_repository import SailorRepository
from src.notifications.context import build_member_context
from src.notifications.contracts import (
    NotificationEligibilityEvaluator,
    NotificationEventRepositoryContract,
    NotificationRouteResolver,
    TriggerDefinitionProvider,
)
from src.notifications.date_utils import local_today
from src.notifications.payloads import NotificationPayloadFactory
from src.notifications.rollout import is_notification_enabled_for_member

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

    async def run_for_date(
            self,
            bot: commands.Bot,
            evaluation_date: date | None = None,
    ) -> int:
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            log.warning("Notification scheduler skipped because the guild is unavailable.")
            return 0

        resolved_date = evaluation_date or local_today()
        created_events = 0
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

                eligibility = self.eligibility_evaluator.evaluate(
                    definition,
                    sailor,
                    member_context,
                    resolved_date,
                )
                if eligibility is None:
                    continue

                route = self.route_resolver.resolve(definition, member_context, guild)
                payload = self.payload_factory.build(
                    definition,
                    sailor,
                    member_context,
                    eligibility,
                )
                _, created = self.event_repository.create_pending_event(
                    definition=definition,
                    sailor=sailor,
                    member_context=member_context,
                    eligibility=eligibility,
                    destination_channel_id=route.destination_channel_id,
                    payload_snapshot=self.payload_factory.to_snapshot(payload),
                )
                if created:
                    created_events += 1

        return created_events
