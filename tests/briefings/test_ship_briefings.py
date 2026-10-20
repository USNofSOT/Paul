import asyncio
import io
import unittest
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from PIL import Image

from src.briefings.daily import (
    ActionItem,
    ChaseEntry,
    ChaseStatus,
    DailyShipBriefing,
    SailorAvatar,
    build_attention_rows,
    build_tasking_messages,
    classify_activity,
    compose_daily_briefing_messages,
    enrich_daily_briefing_avatars,
    render_daily_dashboard_images,
    render_pending_award_embeds,
)
from src.briefings.daily.briefing import _initials, _pressure_summary
from src.briefings.delivery import ShipBriefingRunner
from src.briefings.weekly import (
    build_weekly_briefing,
    compose_weekly_briefing_messages,
    render_activity_image,
    render_crew_image,
)
from src.briefings.weekly.briefing import _format_delta
from src.config.awards import MEDALS_AND_RIBBONS
from src.config.briefings import HOST_CAPABLE_ROLE_IDS
from src.config.subclasses import SUBCLASS_AWARDS
from src.utils.check_awards import PendingShipAward, get_pending_ship_awards

_avatar_buffer = io.BytesIO()
Image.new("RGB", (64, 64), "#4c8dff").save(_avatar_buffer, format="PNG")
TINY_PNG = _avatar_buffer.getvalue()


class DummyRole:
    def __init__(self, role_id, members=None):
        self.id = role_id
        self.members = members or []


class DummyMember:
    def __init__(self, member_id, name, roles, joined_at, avatar=None):
        self.id = member_id
        self.display_name = name
        self.roles = roles
        self.joined_at = joined_at
        self.display_avatar = avatar


class DummyAvatar:
    def __init__(self, *, data=b"", error=None):
        self.data = data
        self.error = error
        self.replace_calls = []
        self.read_calls = 0

    def replace(self, **kwargs):
        self.replace_calls.append(kwargs)
        return self

    async def read(self):
        self.read_calls += 1
        if self.error is not None:
            raise self.error
        return self.data


class DummyChannel:
    def __init__(self):
        self.messages = []

    async def send(self, content=None, **kwargs):
        self.messages.append((content, kwargs))


class DummyGuild:
    def __init__(self, roles, channels, members=None):
        self.roles = roles
        self.channels = channels
        self.members = members or {}

    def get_role(self, role_id):
        return self.roles.get(role_id)

    def get_channel(self, channel_id):
        return self.channels.get(channel_id)

    def get_member(self, member_id):
        return self.members.get(member_id)


class DummyBot:
    def __init__(self, guild):
        self.guild = guild

    def get_guild(self, guild_id):
        del guild_id
        return self.guild


class FakeRepository:
    def __init__(
        self,
        *,
        voyage=None,
        hosting=None,
        role_additions=None,
        sailors=None,
        voyage_counts=None,
        hosting_counts=None,
    ):
        self.voyage = voyage or {}
        self.hosting = hosting or {}
        self.role_additions = role_additions or {}
        self.sailors = sailors or []
        self.voyage_counts = iter(voyage_counts or [0, 0, 0, 0])
        self.hosting_counts = iter(hosting_counts or [0, 0, 0, 0])
        self.voyage_count_calls = 0
        self.hosting_count_calls = 0

    def get_sailors_by_ids(self, sailor_ids):
        del sailor_ids
        return self.sailors

    def get_latest_voyage_activity(self, sailor_ids):
        del sailor_ids
        return self.voyage

    def get_latest_hosting_activity(self, sailor_ids):
        del sailor_ids
        return self.hosting

    def get_latest_ship_role_additions(self, **kwargs):
        del kwargs
        return self.role_additions

    def get_public_service_counts(self, sailor_ids):
        del sailor_ids
        return {}

    def count_voyage_logs_between(self, **kwargs):
        del kwargs
        self.voyage_count_calls += 1
        return next(self.voyage_counts)

    def count_hosting_logs_between(self, **kwargs):
        del kwargs
        self.hosting_count_calls += 1
        return next(self.hosting_counts)


class TestActivityClassification(unittest.TestCase):
    def setUp(self):
        self.reference = datetime(2026, 7, 24, 15, tzinfo=UTC)
        self.member = SimpleNamespace(id=1, display_name="Sailor")

    def test_classifies_due_soon_overdue_current_and_exact_boundary(self):
        due = classify_activity(
            member=self.member,
            activity_at=self.reference - timedelta(days=25),
            baseline_at=self.reference,
            requirement_days=28,
            due_soon_days=7,
            reference_time=self.reference,
        )
        overdue = classify_activity(
            member=self.member,
            activity_at=self.reference - timedelta(days=29),
            baseline_at=self.reference,
            requirement_days=28,
            due_soon_days=7,
            reference_time=self.reference,
        )
        current = classify_activity(
            member=self.member,
            activity_at=self.reference - timedelta(days=5),
            baseline_at=self.reference,
            requirement_days=28,
            due_soon_days=7,
            reference_time=self.reference,
        )
        exact = classify_activity(
            member=self.member,
            activity_at=self.reference - timedelta(days=28),
            baseline_at=self.reference,
            requirement_days=28,
            due_soon_days=7,
            reference_time=self.reference,
        )

        self.assertEqual(due.status, ChaseStatus.DUE_SOON)
        self.assertEqual(due.days, 3)
        self.assertEqual(overdue.status, ChaseStatus.OVERDUE)
        self.assertEqual(overdue.days, 1)
        self.assertIsNone(current)
        self.assertEqual(exact.status, ChaseStatus.DUE_SOON)
        self.assertEqual(exact.days, 0)

    def test_missing_history_tracks_days_without_activity(self):
        entry = classify_activity(
            member=self.member,
            activity_at=None,
            baseline_at=self.reference - timedelta(days=23),
            requirement_days=28,
            due_soon_days=7,
            reference_time=self.reference,
        )
        self.assertEqual(entry.status, ChaseStatus.DUE_SOON)
        self.assertTrue(entry.missing_history)
        self.assertEqual(entry.days, 23)


class TestDailyBriefing(unittest.TestCase):
    def setUp(self):
        self.reference = datetime(2026, 7, 24, 15, tzinfo=UTC)
        self.ship_role = DummyRole(100)
        self.host_role = DummyRole(next(iter(HOST_CAPABLE_ROLE_IDS)))
        self.host = DummyMember(
            1,
            "Host",
            [self.ship_role, self.host_role],
            self.reference - timedelta(days=30),
        )
        self.sailor = DummyMember(
            2,
            "Sailor",
            [self.ship_role],
            self.reference - timedelta(days=30),
        )
        self.ship_role.members = [self.host, self.sailor]
        self.guild = DummyGuild({100: self.ship_role}, {})

    def test_hosting_only_applies_to_host_capable_members(self):
        repository = FakeRepository(
            voyage={
                1: self.reference - timedelta(days=1),
                2: self.reference - timedelta(days=1),
            },
            role_additions={
                1: self.reference - timedelta(days=20),
                2: self.reference - timedelta(days=20),
            },
        )
        runner = ShipBriefingRunner(repository, production=True)
        with patch(
            "src.briefings.daily.briefing._acting_officer_id",
            return_value=None,
        ):
            briefing = runner.build_daily_briefing(
                guild=self.guild,
                ship_role=self.ship_role,
                ship_name="USS Test",
                reference_time=self.reference,
            )
        self.assertEqual(briefing.hosting_overdue, 1)
        self.assertEqual(len(briefing.hosting_chase), 1)
        self.assertEqual(briefing.hosting_chase[0].sailor_id, self.host.id)

    def test_missing_history_action_says_no_activity(self):
        self.ship_role.members = [self.sailor]
        repository = FakeRepository(
            role_additions={
                self.sailor.id: self.reference - timedelta(days=30),
            },
        )
        runner = ShipBriefingRunner(repository, production=True)
        with patch(
            "src.briefings.daily.briefing._acting_officer_id",
            return_value=88,
        ):
            briefing = runner.build_daily_briefing(
                guild=self.guild,
                ship_role=self.ship_role,
                ship_name="USS Test",
                reference_time=self.reference,
            )

        self.assertEqual(len(briefing.requirement_actions), 1)
        self.assertEqual(
            briefing.requirement_actions[0].detail,
            "30d no activity",
        )

    def test_loa_sailor_stays_on_dashboard_without_voyage_tasking(self):
        self.sailor.display_name = "[LOA-1] Sailor"
        self.ship_role.members = [self.sailor]
        repository = FakeRepository(
            voyage={
                self.sailor.id: self.reference - timedelta(days=40),
            },
            role_additions={
                self.sailor.id: self.reference - timedelta(days=50),
            },
        )
        runner = ShipBriefingRunner(repository, production=True)
        with patch(
            "src.briefings.daily.briefing._acting_officer_id",
            return_value=88,
        ) as acting_officer:
            briefing = runner.build_daily_briefing(
                guild=self.guild,
                ship_role=self.ship_role,
                ship_name="USS Test",
                reference_time=self.reference,
            )

        self.assertEqual(briefing.voyage_overdue, 1)
        self.assertEqual(briefing.voyage_chase[0].sailor_id, self.sailor.id)
        self.assertTrue(briefing.voyage_chase[0].on_loa)
        self.assertEqual(briefing.overdue_count, 0)
        self.assertEqual(briefing.requirement_actions, ())
        acting_officer.assert_not_called()

    def test_loa_host_stays_on_dashboard_without_hosting_tasking(self):
        self.host.display_name = "[LOA-2] Host"
        self.ship_role.members = [self.host]
        repository = FakeRepository(
            voyage={self.host.id: self.reference},
            hosting={
                self.host.id: self.reference - timedelta(days=40),
            },
            role_additions={
                self.host.id: self.reference - timedelta(days=50),
            },
        )
        runner = ShipBriefingRunner(repository, production=True)
        with patch(
            "src.briefings.daily.briefing._acting_officer_id",
            return_value=88,
        ) as acting_officer:
            briefing = runner.build_daily_briefing(
                guild=self.guild,
                ship_role=self.ship_role,
                ship_name="USS Test",
                reference_time=self.reference,
            )

        self.assertEqual(briefing.hosting_overdue, 1)
        self.assertTrue(briefing.hosting_chase[0].on_loa)
        self.assertEqual(briefing.loa_hosting_overdue_count, 1)
        self.assertEqual(briefing.overdue_count, 0)
        self.assertEqual(briefing.requirement_actions, ())
        self.assertTrue(build_attention_rows(briefing)[0].is_loa_only)
        acting_officer.assert_not_called()

    def test_dashboard_labels_are_compact_and_ignore_loa_prefixes(self):
        self.assertEqual(_initials("[LOA-1] Seaman Elite"), "SE")
        self.assertEqual(_pressure_summary(overdue=0, due_soon=1), "1 due soon")
        self.assertEqual(
            _pressure_summary(overdue=1, due_soon=0, on_loa=2),
            "1 overdue · 2 on LOA",
        )
        self.assertEqual(_pressure_summary(overdue=0, due_soon=0), "All current")

    def test_awards_and_requirements_keep_separate_actions(self):
        self.guild.members[88] = DummyMember(
            88,
            "CPO Officer",
            [],
            self.reference,
        )
        sailor_record = SimpleNamespace(discord_id=2)
        award = _pending_award()
        repository = FakeRepository(
            voyage={1: self.reference, 2: self.reference - timedelta(days=40)},
            hosting={1: self.reference},
            role_additions={
                1: self.reference - timedelta(days=50),
                2: self.reference - timedelta(days=50),
            },
            sailors=[sailor_record],
        )
        runner = ShipBriefingRunner(repository, production=True)
        with (
            patch(
                "src.briefings.daily.briefing.get_pending_ship_awards",
                return_value=(award,),
            ),
            patch(
                "src.briefings.daily.briefing._acting_officer_id",
                return_value=88,
            ),
        ):
            briefing = runner.build_daily_briefing(
                guild=self.guild,
                ship_role=self.ship_role,
                ship_name="USS Test",
                reference_time=self.reference,
            )

        requirement = next(
            action
            for action in briefing.requirement_actions
            if action.sailor_name == "Sailor"
        )
        award_action = next(
            action
            for action in briefing.award_actions
            if action.sailor_name == "Sailor"
        )
        self.assertEqual(requirement.label, "Voyaging")
        self.assertEqual(requirement.detail, "12d late")
        self.assertEqual(requirement.responsible_id, 88)
        self.assertEqual(requirement.responsible_name, "CPO Officer")
        self.assertEqual(award_action.label, "Award")
        self.assertEqual(award_action.detail, "Voyage Medal")
        self.assertEqual(award_action.responsible_id, 99)
        self.assertEqual(award_action.responsible_name, "Officer")

    def test_daily_briefing_does_not_query_weekly_activity(self):
        repository = FakeRepository(
            voyage={
                1: self.reference - timedelta(days=1),
                2: self.reference - timedelta(days=1),
            },
            hosting={1: self.reference - timedelta(days=1)},
            role_additions={
                1: self.reference - timedelta(days=20),
                2: self.reference - timedelta(days=20),
            },
        )
        runner = ShipBriefingRunner(repository, production=True)
        with patch(
            "src.briefings.daily.briefing._acting_officer_id",
            return_value=None,
        ):
            runner.build_daily_briefing(
                guild=self.guild,
                ship_role=self.ship_role,
                ship_name="USS Test",
                reference_time=self.reference,
            )

        self.assertEqual(repository.voyage_count_calls, 0)
        self.assertEqual(repository.hosting_count_calls, 0)

    def test_attention_rows_consolidate_requirements_and_sort_by_urgency(self):
        briefing = _daily_briefing(
            voyage_chase=(
                ChaseEntry(1, "Both", ChaseStatus.DUE_SOON, 2),
                ChaseEntry(2, "Voyage", ChaseStatus.OVERDUE, 4),
                ChaseEntry(3, "Soon", ChaseStatus.DUE_SOON, 1),
            ),
            hosting_chase=(ChaseEntry(1, "Both", ChaseStatus.OVERDUE, 10),),
        )
        rows = build_attention_rows(briefing)

        self.assertEqual([row.sailor_id for row in rows], [1, 2, 3])
        self.assertEqual(
            [requirement.label for requirement in rows[0].requirements],
            ["Hosting", "Voyaging"],
        )
        self.assertTrue(rows[0].is_overdue)
        self.assertFalse(rows[-1].is_overdue)

    def test_loa_overdue_requirements_are_grey(self):
        loa_voyage = ChaseEntry(
            1,
            "[LOA-1] Sailor",
            ChaseStatus.OVERDUE,
            12,
            on_loa=True,
        )
        loa_only = _daily_briefing(voyage_chase=(loa_voyage,))
        loa_row = build_attention_rows(loa_only)[0]

        self.assertTrue(loa_row.is_loa_only)
        self.assertFalse(loa_row.is_overdue)
        self.assertEqual(loa_only.overdue_count, 0)
        with patch("src.briefings.daily.briefing._draw_status_pill") as draw_pill:
            render_daily_dashboard_images(loa_only)
        self.assertEqual(draw_pill.call_args.kwargs["color"], "#718087")
        self.assertIn("LOA", draw_pill.call_args.kwargs["text"])

        loa_hosting = _daily_briefing(
            hosting_chase=(
                ChaseEntry(
                    2,
                    "[LOA-2] Host",
                    ChaseStatus.OVERDUE,
                    23,
                    on_loa=True,
                ),
            ),
        )
        hosting_row = build_attention_rows(loa_hosting)[0]
        self.assertTrue(hosting_row.is_loa_only)
        self.assertEqual(loa_hosting.overdue_count, 0)
        self.assertEqual(loa_hosting.loa_hosting_overdue_count, 1)

        mixed = _daily_briefing(
            voyage_chase=(loa_voyage,),
            hosting_chase=(
                ChaseEntry(
                    1,
                    "[LOA-1] Sailor",
                    ChaseStatus.OVERDUE,
                    3,
                    on_loa=True,
                ),
            ),
        )
        mixed_row = build_attention_rows(mixed)[0]
        self.assertFalse(mixed_row.is_overdue)
        self.assertTrue(mixed_row.is_loa_only)
        self.assertEqual(mixed.overdue_count, 0)

    def test_dashboard_is_valid_png_and_paginates_after_18_rows(self):
        chase = tuple(
            ChaseEntry(
                sailor_id=index,
                sailor_name=f"Sailor {index}",
                status=ChaseStatus.OVERDUE,
                days=index,
            )
            for index in range(1, 20)
        )
        images = render_daily_dashboard_images(
            _daily_briefing(
                voyage_chase=chase,
                avatars=(SailorAvatar(1, TINY_PNG),),
            )
        )
        self.assertEqual(len(images), 2)
        for image in images:
            self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(len(image), 10_000)

    def test_malformed_avatar_falls_back_without_breaking_dashboard(self):
        briefing = _daily_briefing(
            voyage_chase=(ChaseEntry(1, "Fallback", ChaseStatus.OVERDUE, 2),),
            avatars=(SailorAvatar(1, b"not-an-image"),),
        )
        image = render_daily_dashboard_images(briefing)[0]
        self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_valid_avatar_is_rendered_instead_of_initials(self):
        briefing = _daily_briefing(
            voyage_chase=(ChaseEntry(1, "Avatar", ChaseStatus.OVERDUE, 2),),
            avatars=(SailorAvatar(1, TINY_PNG),),
        )
        with patch("src.briefings.daily.briefing._draw_initials_badge") as fallback:
            render_daily_dashboard_images(briefing)
        fallback.assert_not_called()

    def test_daily_messages_are_situation_then_tasking(self):
        briefing = _daily_briefing(
            awards=(_pending_award(),),
            requirement_actions=(_action(1, "One", "Voyaging", "12d late", 88),),
            award_actions=(_action(1, "One", "Award", "Voyage Medal", 99),),
        )
        with patch(
            "src.briefings.daily.briefing.render_daily_dashboard_images",
            return_value=(b"\x89PNG\r\n\x1a\nfake",),
        ):
            messages = compose_daily_briefing_messages(
                briefing,
                concerns={"requirements": True, "awards": True},
                mentions_enabled=True,
            )

        self.assertEqual(len(messages), 3)
        self.assertEqual(len(messages[0].files), 1)
        self.assertEqual(len(messages[0].embeds), 2)
        self.assertIn("Daily briefing", messages[0].embeds[0].title)
        self.assertIn("Pending awards", messages[0].embeds[1].title)
        award_details = messages[0].embeds[1].fields[0].value
        self.assertIn("Voyage Medal", award_details)
        self.assertIn("Ranks responsible:** `E-6+`", award_details)
        self.assertIn("Responsible CO:** <@99>", award_details)
        self.assertIsNone(messages[0].embeds[0].footer.text)
        self.assertIsNone(messages[0].embeds[1].footer.text)
        self.assertEqual(
            messages[0].embeds[0].color,
            discord.Color.red(),
        )
        self.assertEqual(
            messages[0].embeds[1].color,
            discord.Color.red(),
        )
        self.assertIsNone(messages[1].content)
        self.assertIn("2 actions", messages[1].embeds[0].description)
        self.assertEqual(
            messages[1].embeds[0].color,
            discord.Color.blue(),
        )
        tasking = "\n".join(field.value for field in messages[1].embeds[0].fields)
        self.assertIn("<@1>", tasking)
        self.assertIn("<@1> · **One**", tasking)
        self.assertIn("Voyaging · 12d late", tasking)
        self.assertIn("1 award", tasking)
        self.assertNotIn("Voyage Medal", tasking)
        self.assertIn("<@88>", messages[2].content)
        self.assertIn("<@99>", messages[2].content)
        self.assertIn("daily briefing is ready", messages[2].content)
        self.assertTrue(messages[2].allow_user_mentions)

    def test_disabled_concern_suppresses_visual_and_actions(self):
        briefing = _daily_briefing(
            awards=(_pending_award(),),
            requirement_actions=(
                _action(1, "One", "Voyaging", "12d late", 88),
                _action(1, "One", "Hosting", "4d late", 88),
            ),
            award_actions=(_action(1, "One", "Award", "Voyage Medal", 99),),
        )
        messages = compose_daily_briefing_messages(
            briefing,
            concerns={"requirements": False, "awards": True},
            mentions_enabled=False,
        )

        self.assertEqual(len(messages), 3)
        self.assertFalse(messages[0].files)
        self.assertIn("Pending awards", messages[0].embeds[0].title)
        self.assertIsNone(messages[1].content)
        self.assertIn("1 action", messages[1].embeds[0].description)
        self.assertNotIn("@<88>", messages[2].content)
        self.assertIn("@<99>", messages[2].content)
        self.assertFalse(messages[2].allow_user_mentions)
        self.assertEqual(
            briefing.action_count_for({"requirements": False, "awards": True}),
            1,
        )

        no_messages = compose_daily_briefing_messages(
            briefing,
            concerns={"requirements": False, "awards": False},
            mentions_enabled=False,
        )
        self.assertEqual(no_messages, ())

    def test_awards_only_all_clear_is_always_sent(self):
        messages = compose_daily_briefing_messages(
            _daily_briefing(),
            concerns={"requirements": False, "awards": True},
            mentions_enabled=False,
        )
        self.assertEqual(len(messages), 1)
        self.assertIn("No pending awards", messages[0].embeds[0].description)
        self.assertEqual(
            messages[0].embeds[0].color,
            discord.Color.green(),
        )

    def test_due_soon_sailors_do_not_create_tasking(self):
        messages = compose_daily_briefing_messages(
            _daily_briefing(
                voyage_chase=(ChaseEntry(1, "Soon", ChaseStatus.DUE_SOON, 2),),
            ),
            concerns={"requirements": True, "awards": True},
            mentions_enabled=True,
        )
        self.assertEqual(len(messages), 1)
        self.assertIsNone(messages[0].content)
        self.assertEqual(len(messages[0].embeds), 2)
        self.assertEqual(
            messages[0].embeds[0].color,
            discord.Color.green(),
        )
        self.assertEqual(
            messages[0].embeds[1].color,
            discord.Color.green(),
        )

    def test_tasking_deduplicates_officers_and_aggregates_awards(self):
        actions = (
            _action(
                1,
                "One",
                "Voyaging",
                "12d late",
                99,
                "CPO Officer",
            ),
            _action(
                2,
                "Two",
                "Award",
                "Voyage Medal",
                99,
                "CPO Officer",
            ),
            _action(
                2,
                "Two",
                "Award",
                "Service Medal",
                99,
                "CPO Officer",
            ),
            _action(
                2,
                "Two",
                "Hosting",
                "4d late",
                100,
                "Lieutenant Officer",
            ),
            _action(3, "Three", "Award", "Subclass Medal", None),
        )
        messages = build_tasking_messages(actions, ship_name="USS Test")
        self.assertEqual(len(messages), 2)
        self.assertIsNone(messages[0].content)
        fields = messages[0].embeds[0].fields
        values = "\n".join(field.value for field in fields)
        self.assertIn("<@1>", values)
        self.assertIn("<@2>", values)
        self.assertIn("<@3>", values)
        self.assertIn("<@1> · **One**", values)
        self.assertIn("<@2> · **Two**", values)
        self.assertIn("<@3> · **Three**", values)
        self.assertIn("Voyaging · 12d late", values)
        self.assertIn("2 awards", values)
        self.assertNotIn("Voyage Medal", values)
        self.assertTrue(any("Unassigned" in field.name for field in fields))
        self.assertTrue(any("CPO Officer" in field.name for field in fields))
        self.assertTrue(any("Lieutenant Officer" in field.name for field in fields))
        hosting_field = next(
            field for field in fields if "Lieutenant Officer" in field.name
        )
        self.assertIn("<@2> · **Two**", hosting_field.value)
        self.assertIn("Hosting · 4d late", hosting_field.value)
        self.assertFalse(any("<@99>" in field.name for field in fields))
        self.assertFalse(any("<@100>" in field.name for field in fields))
        self.assertEqual(messages[1].content.count("<@99>"), 1)
        self.assertEqual(messages[1].content.count("<@100>"), 1)

        disabled_messages = build_tasking_messages(
            actions,
            ship_name="USS Test",
            mentions_enabled=False,
        )
        disabled_values = "\n".join(
            field.value for field in disabled_messages[0].embeds[0].fields
        )
        self.assertIn("@<1>", disabled_values)
        self.assertNotIn("<@1>", disabled_values)
        self.assertIn("@<1> · **One**", disabled_values)
        self.assertIn("@<2> · **Two**", disabled_values)
        disabled_content = disabled_messages[1].content
        self.assertEqual(disabled_content.count("@<99>"), 1)
        self.assertEqual(disabled_content.count("@<100>"), 1)
        self.assertNotIn("<@99>", disabled_content)
        self.assertNotIn("<@100>", disabled_content)

    def test_tasking_and_situation_paginate_at_discord_limits(self):
        actions = tuple(
            _action(
                officer_id,
                f"Sailor {officer_id}",
                "Voyaging",
                "1d late",
                officer_id,
            )
            for officer_id in range(1, 27)
        )
        tasking = build_tasking_messages(actions, ship_name="USS Test")
        self.assertEqual(len(tasking), 2)
        self.assertEqual(len(tasking[0].embeds), 2)
        self.assertEqual(len(tasking[0].embeds[0].fields), 25)
        self.assertEqual(len(tasking[0].embeds[1].fields), 1)
        self.assertFalse(tasking[1].embeds)

        briefing = _daily_briefing(awards=(_pending_award(),))
        award_embeds = tuple(
            discord.Embed(title=f"Awards {index}") for index in range(11)
        )
        with patch(
            "src.briefings.daily.briefing.render_pending_award_embeds",
            return_value=award_embeds,
        ):
            situation = compose_daily_briefing_messages(
                briefing,
                concerns={"requirements": False, "awards": True},
                mentions_enabled=False,
            )
        self.assertEqual(len(situation), 2)
        self.assertEqual(len(situation[0].embeds), 10)
        self.assertEqual(len(situation[1].embeds), 1)

        long_award_embeds = tuple(
            discord.Embed(description="x" * 2_500) for _ in range(3)
        )
        with patch(
            "src.briefings.daily.briefing.render_pending_award_embeds",
            return_value=long_award_embeds,
        ):
            situation = compose_daily_briefing_messages(
                briefing,
                concerns={"requirements": False, "awards": True},
                mentions_enabled=False,
            )
        self.assertEqual([len(message.embeds) for message in situation], [2, 1])
        self.assertTrue(
            all(
                sum(len(embed) for embed in message.embeds) <= 6_000
                for message in situation
            )
        )

    def test_pending_awards_paginate_without_splitting_entries(self):
        awards = tuple(
            PendingShipAward(
                sailor_id=index,
                sailor_name=f"Sailor {index // 3}",
                award_name=f"Award {index}",
                details_url=f"https://example.com/awards/{index}",
                ranks_responsible="E-6+",
                responsible_id=99,
            )
            for index in range(23)
        )

        embeds = render_pending_award_embeds(
            awards,
            subject_name="USS Test",
        )

        self.assertEqual(len(embeds), 3)
        self.assertEqual(
            [len(embed.fields) for embed in embeds],
            [10, 10, 3],
        )
        self.assertIn("1/3", embeds[0].title)
        self.assertIn("21–23", embeds[2].description)
        rendered_values = [field.value for embed in embeds for field in embed.fields]
        self.assertEqual(len(rendered_values), 23)
        rendered_text = "\n".join(rendered_values)
        for index in range(23):
            self.assertIn(f"Award {index}", rendered_text)
            self.assertIn(f"/awards/{index}", rendered_text)
        for value in rendered_values:
            self.assertIn("Ranks responsible", value)
            self.assertIn("Responsible CO", value)
        self.assertEqual(embeds[0].fields[0].name, "Sailor 0")

    def test_pending_awards_cover_ship_award_categories(self):
        award_groups = (
            MEDALS_AND_RIBBONS.voyages,
            MEDALS_AND_RIBBONS.hosted,
            MEDALS_AND_RIBBONS.public_service,
            SUBCLASS_AWARDS.cannoneer,
            SUBCLASS_AWARDS.carpenter,
            SUBCLASS_AWARDS.flex,
            SUBCLASS_AWARDS.helm,
            SUBCLASS_AWARDS.grenadier,
            SUBCLASS_AWARDS.surgeon,
        )
        roles = {
            award.role_id: SimpleNamespace(
                id=award.role_id,
                name=f"Award {award.role_id}",
            )
            for awards in award_groups
            for award in awards
        }
        guild = DummyGuild(roles, {})
        member = DummyMember(10, "Award Sailor", [], self.reference)
        sailor = SimpleNamespace(
            voyage_count=MEDALS_AND_RIBBONS.voyages[0].threshold,
            force_voyage_count=0,
            hosted_count=MEDALS_AND_RIBBONS.hosted[0].threshold,
            force_hosted_count=0,
            cannoneer_points=SUBCLASS_AWARDS.cannoneer[0].threshold,
            force_cannoneer_points=0,
            carpenter_points=SUBCLASS_AWARDS.carpenter[0].threshold,
            force_carpenter_points=0,
            flex_points=SUBCLASS_AWARDS.flex[0].threshold,
            force_flex_points=0,
            helm_points=SUBCLASS_AWARDS.helm[0].threshold,
            force_helm_points=0,
            grenadier_points=SUBCLASS_AWARDS.grenadier[0].threshold,
            force_grenadier_points=0,
            surgeon_points=SUBCLASS_AWARDS.surgeon[0].threshold,
            force_surgeon_points=0,
        )
        awards = get_pending_ship_awards(
            guild,
            sailor,
            member,
            public_service_count=MEDALS_AND_RIBBONS.public_service[0].threshold,
        )
        self.assertEqual(len(awards), 9)
        self.assertTrue(all(award.ranks_responsible for award in awards))


class TestAvatarEnrichment(unittest.IsolatedAsyncioTestCase):
    async def test_fetches_each_attention_sailor_once(self):
        avatar = DummyAvatar(data=TINY_PNG)
        member = DummyMember(
            1,
            "Both",
            [],
            datetime(2026, 7, 1, tzinfo=UTC),
            avatar=avatar,
        )
        briefing = _daily_briefing(
            voyage_chase=(ChaseEntry(1, "Both", ChaseStatus.OVERDUE, 2),),
            hosting_chase=(ChaseEntry(1, "Both", ChaseStatus.DUE_SOON, 1),),
        )

        enriched = await enrich_daily_briefing_avatars(
            briefing,
            members=(member,),
        )

        self.assertEqual(avatar.read_calls, 1)
        self.assertEqual(
            avatar.replace_calls,
            [{"size": 64, "format": "png", "static_format": "png"}],
        )
        self.assertEqual(enriched.avatars, (SailorAvatar(1, TINY_PNG),))

    async def test_timeout_falls_back_to_initials(self):
        avatar = DummyAvatar()

        async def slow_read():
            await asyncio.sleep(1)
            return TINY_PNG

        avatar.read = slow_read
        member = DummyMember(
            1,
            "Slow",
            [],
            datetime(2026, 7, 1, tzinfo=UTC),
            avatar=avatar,
        )
        briefing = _daily_briefing(
            voyage_chase=(ChaseEntry(1, "Slow", ChaseStatus.OVERDUE, 2),),
        )

        enriched = await enrich_daily_briefing_avatars(
            briefing,
            members=(member,),
            timeout_seconds=0.001,
        )

        self.assertEqual(enriched.avatars, ())

    async def test_failed_avatar_does_not_fail_other_sailors(self):
        good = DummyAvatar(data=TINY_PNG)
        bad = DummyAvatar(error=RuntimeError("cdn unavailable"))
        members = (
            DummyMember(1, "Good", [], None, avatar=good),
            DummyMember(2, "Bad", [], None, avatar=bad),
        )
        briefing = _daily_briefing(
            voyage_chase=(
                ChaseEntry(1, "Good", ChaseStatus.OVERDUE, 2),
                ChaseEntry(2, "Bad", ChaseStatus.OVERDUE, 1),
            ),
        )

        enriched = await enrich_daily_briefing_avatars(
            briefing,
            members=members,
        )

        self.assertEqual(enriched.avatars, (SailorAvatar(1, TINY_PNG),))


class TestWeeklyBriefing(unittest.TestCase):
    def setUp(self):
        repository = MagicMock()
        repository.count_voyage_logs_between.side_effect = [1, 2, 3, 4]
        repository.count_hosting_logs_between.side_effect = [4, 3, 2, 1]
        repository.get_ship_size_on_or_before.side_effect = [7, 8, 9]
        self.briefing = build_weekly_briefing(
            repository,
            ship_role_id=100,
            ship_name="USS Test",
            current_ship_size=11,
            reference_time=datetime(2026, 7, 24, 9, tzinfo=UTC),
        )

    def test_builds_exactly_four_weekly_points(self):
        self.assertEqual(len(self.briefing.points), 4)
        self.assertEqual(
            [point.voyage_count for point in self.briefing.points],
            [1, 2, 3, 4],
        )
        self.assertEqual(self.briefing.points[-1].crew_size, 11)
        self.assertEqual(
            [point.period_end for point in self.briefing.points],
            [
                date(2026, 7, 3),
                date(2026, 7, 10),
                date(2026, 7, 17),
                date(2026, 7, 24),
            ],
        )

    def test_weekly_images_are_valid_png(self):
        for image in (
            render_activity_image(self.briefing),
            render_crew_image(self.briefing),
        ):
            self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(len(image), 10_000)

    def test_weekly_delta_labels_are_readable(self):
        self.assertEqual(_format_delta(47, 67), "↓ 20 WoW")
        self.assertEqual(_format_delta(18, 14), "↑ 4 WoW")
        self.assertEqual(_format_delta(25, 25), "No change")

    def test_weekly_concerns_are_separate_and_ordered(self):
        messages = compose_weekly_briefing_messages(
            self.briefing,
            concerns={"activity": True, "crew": True},
        )
        self.assertEqual(len(messages), 2)
        self.assertTrue(messages[0].files[0].filename.startswith("weekly_activity"))
        self.assertTrue(messages[1].files[0].filename.startswith("weekly_crew"))

        activity_only = compose_weekly_briefing_messages(
            self.briefing,
            concerns={"activity": True, "crew": False},
        )
        self.assertEqual(len(activity_only), 1)
        self.assertTrue(
            activity_only[0].files[0].filename.startswith("weekly_activity")
        )


class TestDelivery(unittest.IsolatedAsyncioTestCase):
    async def test_unavailable_guild_does_not_page_engineers(self):
        runner = ShipBriefingRunner(FakeRepository())
        ship = _ship(100, "USS Test", 600)

        with (
            patch("src.briefings.delivery.SHIPS", (ship,)),
            patch("src.briefings.delivery.log") as delivery_log,
        ):
            summary = await runner.send_daily_briefings(DummyBot(None))

        self.assertEqual(summary.failed_count, 1)
        extra = delivery_log.warning.call_args.kwargs["extra"]
        self.assertNotIn("notify_engineer", extra)

    async def test_manual_message_target_does_not_require_a_channel(self):
        message_target = DummyChannel()
        ship_role = DummyRole(100)
        guild = DummyGuild({100: ship_role}, {})
        ship = _ship(100, "USS Test", 600)
        runner = ShipBriefingRunner(
            FakeRepository(),
            production=False,
            user_mentions_enabled=True,
            daily_concerns={"requirements": False, "awards": True},
        )
        with (
            patch("src.briefings.delivery.SHIPS", (ship,)),
            patch.object(
                runner,
                "build_daily_briefing",
                return_value=_daily_briefing(
                    awards=(_pending_award(),),
                    award_actions=(_action(1, "One", "Award", "Voyage Medal", 99),),
                ),
            ),
        ):
            summary = await runner.send_daily_briefings(
                DummyBot(guild),
                message_target=message_target,
            )

        self.assertEqual(summary.sent_count, 1)
        self.assertEqual(len(message_target.messages), 3)
        _, tasking_kwargs = message_target.messages[1]
        tasking_values = "\n".join(
            field.value for field in tasking_kwargs["embeds"][0].fields
        )
        self.assertIn("<@1>", tasking_values)
        content, reminder_kwargs = message_target.messages[2]
        self.assertIn("<@99>", content)
        self.assertTrue(reminder_kwargs["allowed_mentions"].users)

    async def test_nonproduction_uses_preview_channel_and_never_pings(self):
        preview_channel = DummyChannel()
        ship_role = DummyRole(100)
        guild = DummyGuild({100: ship_role}, {500: preview_channel})
        ship = _ship(100, "USS Test", 600)
        runner = ShipBriefingRunner(
            FakeRepository(),
            production=False,
            preview_channel_id=500,
            daily_concerns={"requirements": False, "awards": True},
        )
        with (
            patch("src.briefings.delivery.SHIPS", (ship,)),
            patch.object(
                runner,
                "build_daily_briefing",
                return_value=_daily_briefing(
                    awards=(_pending_award(),),
                    award_actions=(_action(1, "One", "Award", "Voyage Medal", 99),),
                ),
            ),
        ):
            summary = await runner.send_daily_briefings(DummyBot(guild))

        self.assertEqual(summary.sent_count, 1)
        self.assertEqual(len(preview_channel.messages), 3)
        tasking_content, tasking_kwargs = preview_channel.messages[1]
        self.assertIsNone(tasking_content)
        tasking_values = "\n".join(
            field.value for field in tasking_kwargs["embeds"][0].fields
        )
        self.assertIn("@<1>", tasking_values)
        content, kwargs = preview_channel.messages[2]
        self.assertFalse(kwargs["allowed_mentions"].users)
        self.assertIn("@<99>", content)
        self.assertNotIn("<@99>", content)

    async def test_live_action_message_enables_user_mentions(self):
        live_channel = DummyChannel()
        ship_role = DummyRole(100)
        guild = DummyGuild({100: ship_role}, {600: live_channel})
        ship = _ship(100, "USS Test", 600)
        runner = ShipBriefingRunner(
            FakeRepository(),
            production=True,
            daily_concerns={"requirements": False, "awards": True},
        )
        with (
            patch("src.briefings.delivery.SHIPS", (ship,)),
            patch.object(
                runner,
                "build_daily_briefing",
                return_value=_daily_briefing(
                    awards=(_pending_award(),),
                    award_actions=(_action(1, "One", "Award", "Voyage Medal", 99),),
                ),
            ),
        ):
            await runner.send_daily_briefings(DummyBot(guild))

        self.assertEqual(len(live_channel.messages), 3)
        tasking_content, tasking_kwargs = live_channel.messages[1]
        self.assertIsNone(tasking_content)
        tasking_values = "\n".join(
            field.value for field in tasking_kwargs["embeds"][0].fields
        )
        self.assertIn("<@1>", tasking_values)
        content, kwargs = live_channel.messages[2]
        self.assertTrue(kwargs["allowed_mentions"].users)
        self.assertIn("<@99>", content)

    async def test_requirements_run_enriches_attention_avatars(self):
        preview_channel = DummyChannel()
        member = DummyMember(1, "One", [], None)
        ship_role = DummyRole(100, [member])
        guild = DummyGuild({100: ship_role}, {500: preview_channel})
        ship = _ship(100, "USS Test", 600)
        briefing = _daily_briefing()
        runner = ShipBriefingRunner(
            FakeRepository(),
            production=False,
            preview_channel_id=500,
            daily_concerns={"requirements": True, "awards": False},
        )
        with (
            patch("src.briefings.delivery.SHIPS", (ship,)),
            patch.object(
                runner,
                "build_daily_briefing",
                return_value=briefing,
            ),
            patch(
                "src.briefings.delivery.enrich_daily_briefing_avatars",
                new=AsyncMock(return_value=briefing),
            ) as enrich,
            patch(
                "src.briefings.delivery.compose_daily_briefing_messages",
                return_value=(),
            ),
        ):
            await runner.send_daily_briefings(DummyBot(guild))

        enrich.assert_awaited_once_with(briefing, members=[member])

    async def test_failure_for_one_ship_does_not_block_the_next(self):
        preview_channel = DummyChannel()
        roles = {100: DummyRole(100), 200: DummyRole(200)}
        guild = DummyGuild(roles, {500: preview_channel})
        ships = (
            _ship(100, "USS One", 600),
            _ship(200, "USS Two", 700),
        )
        runner = ShipBriefingRunner(
            FakeRepository(),
            production=False,
            preview_channel_id=500,
            daily_concerns={"requirements": False, "awards": True},
        )
        with (
            patch("src.briefings.delivery.SHIPS", ships),
            patch.object(
                runner,
                "build_daily_briefing",
                side_effect=(RuntimeError("broken"), _daily_briefing()),
            ),
            patch("src.briefings.delivery.log") as delivery_log,
        ):
            summary = await runner.send_daily_briefings(DummyBot(guild))

        self.assertEqual(summary.sent_count, 1)
        self.assertEqual(summary.failed_count, 1)
        self.assertEqual(len(preview_channel.messages), 1)
        self.assertTrue(
            delivery_log.exception.call_args.kwargs["extra"]["notify_engineer"]
        )

    async def test_manual_run_can_target_one_ship(self):
        preview_channel = DummyChannel()
        roles = {100: DummyRole(100), 200: DummyRole(200)}
        guild = DummyGuild(roles, {500: preview_channel})
        ships = (
            _ship(100, "USS One", 600),
            _ship(200, "USS Two", 700),
        )
        runner = ShipBriefingRunner(
            FakeRepository(),
            production=False,
            preview_channel_id=500,
            daily_concerns={"requirements": False, "awards": True},
        )
        with (
            patch("src.briefings.delivery.SHIPS", ships),
            patch.object(
                runner,
                "build_daily_briefing",
                return_value=_daily_briefing(),
            ) as build_report,
        ):
            summary = await runner.send_daily_briefings(
                DummyBot(guild),
                ship_role_ids={200},
            )

        self.assertEqual(summary.sent_count, 1)
        self.assertEqual(build_report.call_count, 1)
        self.assertEqual(build_report.call_args.kwargs["ship_role"].id, 200)


def _pending_award() -> PendingShipAward:
    return PendingShipAward(
        sailor_id=1,
        sailor_name="One",
        award_name="Voyage Medal",
        details_url="https://example.com",
        ranks_responsible="E-6+",
        responsible_id=99,
        responsible_name="Officer",
    )


def _action(
    sailor_id: int,
    sailor_name: str,
    label: str,
    detail: str,
    responsible_id: int | None,
    responsible_name: str | None = None,
) -> ActionItem:
    return ActionItem(
        sailor_id=sailor_id,
        sailor_name=sailor_name,
        label=label,
        detail=detail,
        responsible_id=responsible_id,
        responsible_name=responsible_name,
    )


def _daily_briefing(
    *,
    voyage_chase=(),
    hosting_chase=(),
    awards=(),
    requirement_actions=(),
    award_actions=(),
    avatars=(),
) -> DailyShipBriefing:
    voyage_overdue = sum(entry.status == ChaseStatus.OVERDUE for entry in voyage_chase)
    voyage_due_soon = sum(
        entry.status == ChaseStatus.DUE_SOON for entry in voyage_chase
    )
    hosting_overdue = sum(
        entry.status == ChaseStatus.OVERDUE for entry in hosting_chase
    )
    hosting_due_soon = sum(
        entry.status == ChaseStatus.DUE_SOON for entry in hosting_chase
    )
    return DailyShipBriefing(
        ship_role_id=100,
        ship_name="USS Test",
        reference_time=datetime(2026, 7, 24, 15, tzinfo=UTC),
        voyage_due_soon=voyage_due_soon,
        voyage_overdue=voyage_overdue,
        voyage_current=10,
        hosting_due_soon=hosting_due_soon,
        hosting_overdue=hosting_overdue,
        hosting_current=3,
        voyage_chase=tuple(voyage_chase),
        hosting_chase=tuple(hosting_chase),
        pending_awards=tuple(awards),
        requirement_actions=tuple(requirement_actions),
        award_actions=tuple(award_actions),
        avatars=tuple(avatars),
    )


def _ship(role_id: int, name: str, channel_id: int):
    return SimpleNamespace(
        role_id=role_id,
        name=name,
        boat_command_channel_id=channel_id,
    )
