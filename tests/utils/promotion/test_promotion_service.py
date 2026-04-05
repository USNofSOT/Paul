import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from src.config.awards import (
    FOUR_MONTHS_SERVICE_STRIPES,
    HONORABLE_CONDUCT,
    LEGION_OF_CONDUCT,
    MARITIME_SERVICE_MEDAL,
    NCO_IMPROVEMENT_RIBBON,
)
from src.config.netc_server import (
    COSA_GRADUATE_ROLE,
    OCS_GRADUATE_ROLE,
    SLA_GRADUATE_ROLE,
    SNLA_GRADUATE_ROLE,
)
from src.config.ranks_roles import (
    E6_ROLES,
    NAVAL_SPECIALIST_ROLE,
    O1_ROLES,
    O4_ROLES,
    O5_ROLES,
    SHIP_SL_ROLE,
    SPD_ROLES,
    SQUAD_XO_ROLE,
)
from src.data import RoleChangeType
from src.utils.promotion.models import PromotionContext
from src.utils.promotion.service import build_default_promotion_check_service
from src.utils.rank_and_promotion_utils import get_rank_by_index


def make_role(role_id: int) -> SimpleNamespace:
    return SimpleNamespace(id=role_id)


class FakeAuditLogRepository:
    def __init__(self, role_logs: dict[int, SimpleNamespace] | None = None) -> None:
        self.role_logs = role_logs or {}

    def get_latest_role_log_for_target_and_role(
            self,
            target_id: int,
            role_id: int,
    ) -> SimpleNamespace | None:
        return self.role_logs.get(role_id)


class FakeVoyageRepository:
    def __init__(self, last_voyage_at: datetime | None = None) -> None:
        self.last_voyage_at = last_voyage_at

    def get_last_voyage_by_target_ids(self, target_ids: list[int]) -> dict[int, datetime]:
        if self.last_voyage_at is None:
            return {}
        return {target_ids[0]: self.last_voyage_at}


class PromotionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = build_default_promotion_check_service()
        self.now = datetime(2026, 4, 5, tzinfo=timezone.utc)

    def make_context(
            self,
            current_rank_index: int,
            role_ids: set[int],
            *,
            netc_role_ids: set[int] | None = None,
            voyage_count: int = 0,
            hosted_count: int = 0,
            role_logs: dict[int, SimpleNamespace] | None = None,
            last_voyage_at: datetime | None = None,
    ) -> PromotionContext:
        member = SimpleNamespace(
            roles=[make_role(role_id) for role_id in role_ids],
            display_name="Test Sailor",
        )
        return PromotionContext(
            guild_member=member,
            guild_member_role_ids=role_ids,
            netc_guild_member_role_ids=netc_role_ids or set(),
            target_id=12345,
            voyage_count=voyage_count,
            hosted_count=hosted_count,
            current_rank=get_rank_by_index(current_rank_index),
            is_marine=False,
            audit_log_repository=FakeAuditLogRepository(role_logs),
            voyage_repository=FakeVoyageRepository(last_voyage_at),
            now=self.now,
        )

    def test_e4_to_e6_uses_updated_requirements_and_squad_xo_branch(self) -> None:
        context = self.make_context(
            4,
            {
                LEGION_OF_CONDUCT.role_id,
                NCO_IMPROVEMENT_RIBBON.role_id,
                SPD_ROLES[0],
                SQUAD_XO_ROLE,
            },
            netc_role_ids={SLA_GRADUATE_ROLE},
            hosted_count=10,
        )

        rendered_sections = self.service.evaluate(context)

        self.assertEqual(len(rendered_sections), 1)
        required_field, additional_field = rendered_sections[0].fields
        self.assertIn("Petty Officer", required_field.name)
        self.assertIn(f"<@&{LEGION_OF_CONDUCT.role_id}>", required_field.value)
        self.assertIn(f"<@&{NCO_IMPROVEMENT_RIBBON.role_id}>", required_field.value)
        self.assertIn("SLA Graduate", required_field.value)
        self.assertIn("Hosted ten voyages (10/10)", required_field.value)
        self.assertIn("Joined an SPD", additional_field.value)
        self.assertNotIn("Naval Specialist", additional_field.value)
        self.assertIn(
            "Applied for XO to a squad or became a squad leader (when available)",
            additional_field.value,
        )

    def test_e6_to_e7_uses_one_month_requirement(self) -> None:
        context = self.make_context(
            5,
            {E6_ROLES[0], SHIP_SL_ROLE},
            hosted_count=20,
            role_logs={
                E6_ROLES[0]: SimpleNamespace(
                    log_time=datetime(2026, 2, 15, tzinfo=timezone.utc),
                    change_type=RoleChangeType.ADDED,
                )
            },
        )

        rendered_sections = self.service.evaluate(context)
        required_field, additional_field = rendered_sections[0].fields

        self.assertIn("Waited one month as an E-6", required_field.value)
        self.assertIn("Hosted twenty voyages (20/20)", required_field.value)
        self.assertIn("Passed the SNCO Board", required_field.value)
        self.assertIn("Joined an SPD or became a Naval Specialist", additional_field.value)

    def test_naval_specialist_role_satisfies_specialist_branch(self) -> None:
        context = self.make_context(
            5,
            {E6_ROLES[0], NAVAL_SPECIALIST_ROLE},
            hosted_count=20,
            role_logs={
                E6_ROLES[0]: SimpleNamespace(
                    log_time=datetime(2026, 2, 15, tzinfo=timezone.utc),
                    change_type=RoleChangeType.ADDED,
                )
            },
        )

        rendered_sections = self.service.evaluate(context)
        additional_field = rendered_sections[0].fields[1]

        self.assertIn(
            ":white_check_mark: Joined an SPD or became a Naval Specialist",
            additional_field.value,
        )

    def test_e7_to_e8_has_no_spd_or_cos_additional_requirements(self) -> None:
        context = self.make_context(
            6,
            {
                HONORABLE_CONDUCT.role_id,
                FOUR_MONTHS_SERVICE_STRIPES.role_id,
                NAVAL_SPECIALIST_ROLE,
            },
            netc_role_ids={COSA_GRADUATE_ROLE},
        )

        rendered_sections = self.service.evaluate(context)
        e8_section = rendered_sections[0]

        self.assertEqual(len(e8_section.fields), 1)
        self.assertNotIn("SPD", e8_section.fields[0].value)
        self.assertNotIn("CoS", e8_section.fields[0].value)

    def test_e7_dual_path_renders_both_e8_and_o1(self) -> None:
        context = self.make_context(
            6,
            {
                HONORABLE_CONDUCT.role_id,
                FOUR_MONTHS_SERVICE_STRIPES.role_id,
                SPD_ROLES[0],
            },
            netc_role_ids={COSA_GRADUATE_ROLE},
            hosted_count=35,
        )

        rendered_sections = self.service.evaluate(context)

        self.assertEqual(len(rendered_sections), 2)
        self.assertTrue(rendered_sections[0].show_or_separator_after)
        self.assertIn("Senior Chief Petty Officer", rendered_sections[0].fields[0].name)
        self.assertIn("Midshipman", rendered_sections[1].fields[0].name)
        self.assertIn("Passed the Officer Board", rendered_sections[1].fields[0].value)
        self.assertEqual(len(rendered_sections[1].fields), 1)

    def test_snla_alone_does_not_satisfy_cosa_requirement(self) -> None:
        context = self.make_context(
            8,
            {HONORABLE_CONDUCT.role_id, FOUR_MONTHS_SERVICE_STRIPES.role_id},
            netc_role_ids={SNLA_GRADUATE_ROLE},
            hosted_count=35,
        )

        rendered_sections = self.service.evaluate(context)
        required_field = rendered_sections[0].fields[0]

        self.assertIn(":x: Is a COSA Graduate", required_field.value)

    def test_o1_to_o3_unaffected_path_still_works(self) -> None:
        context = self.make_context(
            9,
            {O1_ROLES[0]},
            netc_role_ids={OCS_GRADUATE_ROLE},
            role_logs={
                O1_ROLES[0]: SimpleNamespace(
                    log_time=datetime(2026, 3, 1, tzinfo=timezone.utc),
                    change_type=RoleChangeType.ADDED,
                )
            },
        )

        rendered_sections = self.service.evaluate(context)
        required_field = rendered_sections[0].fields[0]

        self.assertIn("Waited two weeks as an O1", required_field.value)
        self.assertIn("Is an OCS Graduate", required_field.value)

    def test_o4_to_o5_and_o5_to_o6_use_new_time_thresholds(self) -> None:
        o4_context = self.make_context(
            11,
            {O4_ROLES[0]},
            role_logs={
                O4_ROLES[0]: SimpleNamespace(
                    log_time=datetime(2026, 3, 5, tzinfo=timezone.utc),
                    change_type=RoleChangeType.ADDED,
                )
            },
        )
        o5_context = self.make_context(
            12,
            {O5_ROLES[0], MARITIME_SERVICE_MEDAL.role_id},
            role_logs={
                O5_ROLES[0]: SimpleNamespace(
                    log_time=datetime(2025, 12, 31, tzinfo=timezone.utc),
                    change_type=RoleChangeType.ADDED,
                )
            },
        )

        o4_required = self.service.evaluate(o4_context)[0].fields[0].value
        o5_section = self.service.evaluate(o5_context)[0]
        o5_required = o5_section.fields[0].value

        self.assertIn("Waited four weeks as an O4", o4_required)
        self.assertIn("Waited three months as an O5", o5_required)
        self.assertIn(f"<@&{MARITIME_SERVICE_MEDAL.role_id}>", o5_required)
        self.assertIn("Built a full chain of command", o5_required)
        self.assertEqual(len(o5_section.fields), 1)

    def test_admiralty_paths_render_manual_requirements_with_flavor_notes(self) -> None:
        commodore_section = self.service.evaluate(self.make_context(13, set()))[0]
        rear_admiral_section = self.service.evaluate(self.make_context(14, set()))[0]
        aotn_section = self.service.evaluate(self.make_context(15, set()))[0]

        self.assertEqual(len(commodore_section.fields), 2)
        self.assertIn("Selected by AOTN", commodore_section.fields[0].value)
        self.assertIn("Notes - Commodore", commodore_section.fields[1].name)
        self.assertEqual(len(rear_admiral_section.fields), 2)
        self.assertIn("Selected by AOTN", rear_admiral_section.fields[0].value)
        self.assertIn("No longer commands a ship", rear_admiral_section.fields[0].value)
        self.assertIn("Notes - Rear Admiral", rear_admiral_section.fields[1].name)
        self.assertEqual(len(aotn_section.fields), 2)
        self.assertIn(
            "Hand selected by previous AOTN or by BOA vote should one not have been selected",
            aotn_section.fields[0].value,
        )
        self.assertIn("Notes - Admiral Of The Navy", aotn_section.fields[1].name)


if __name__ == "__main__":
    unittest.main()
