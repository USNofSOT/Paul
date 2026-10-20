import unittest
from datetime import UTC, datetime
from types import SimpleNamespace

from src.cogs.commands.JE.representation import _format_mutation
from src.cogs.commands.SPD.dumprepmutations import (
    build_representation_dump_csv,
    normalize_representation_dump_department,
)
from src.cogs.commands.SPD.representationmod import (
    build_representation_mod_result_embed,
    get_representation_actor_role_ids,
    validate_representation_mutation_request,
)
from src.data.models import RepresentationDepartment, RepresentationPointMutation, RepresentationPoints


class TestRepresentationFormatting(unittest.TestCase):
    def test_format_mutation_uses_discord_relative_timestamp(self) -> None:
        # Arrange
        mutation = RepresentationPointMutation(
            target_id=1,
            changed_by_id=2,
            department=RepresentationDepartment.MEDIA,
            points_delta=3,
            reason="Great work",
            created_at=datetime(2026, 6, 7, 10, 30, tzinfo=UTC),
        )

        # Act
        formatted = _format_mutation(mutation)

        # Assert
        self.assertIn("`+3` Media by <@2>", formatted)
        self.assertIn("(<t:1780828200:R>)", formatted)
        self.assertIn("> Great work", formatted)
        self.assertNotIn("ago", formatted)

    def test_representation_mod_result_embed_is_compact(self) -> None:
        # Arrange
        target = SimpleNamespace(display_name="Sailor", mention="<@123>")
        actor = SimpleNamespace(mention="<@456>")

        # Act
        embed = build_representation_mod_result_embed(
            target=target,
            actor=actor,
            action="Added `2` Media point(s).",
            new_total_count=7,
        )

        # Assert
        self.assertEqual(embed.title, "Representation updated for Sailor")
        self.assertEqual(embed.description, "<@123>")
        self.assertEqual(len(embed.fields), 3)
        self.assertEqual(embed.fields[0].name, "Action")
        self.assertEqual(embed.fields[0].value, "Added `2` Media point(s).")
        self.assertEqual(embed.fields[1].name, "Updated By")
        self.assertEqual(embed.fields[1].value, "<@456>")
        self.assertEqual(embed.fields[2].name, "New Total Count")
        self.assertEqual(embed.fields[2].value, "7")

    def test_get_representation_actor_role_ids_includes_spd_roles(self) -> None:
        # Arrange
        interaction_member = SimpleNamespace(roles=[SimpleNamespace(id=10), SimpleNamespace(id=20)])
        spd_member = SimpleNamespace(roles=[SimpleNamespace(id=20), SimpleNamespace(id=30)])

        # Act
        role_ids = get_representation_actor_role_ids(interaction_member, spd_member)

        # Assert
        self.assertEqual(role_ids, {10, 20, 30})

    def test_validate_representation_mutation_request_requires_exactly_one_action(self) -> None:
        # Act & Assert
        self.assertEqual(
            validate_representation_mutation_request(add=None, remove=None, department=None, reason=None),
            (
                "Missing Action",
                "Use either `add` or `remove` to modify representation points.",
            ),
        )
        self.assertEqual(
            validate_representation_mutation_request(add=1, remove=1, department="Media", reason="Because"),
            (
                "Invalid Input",
                "Use either `add` or `remove`, not both.",
            ),
        )

    def test_normalize_representation_dump_department_accepts_known_values(self) -> None:
        # Act & Assert
        self.assertIsNone(normalize_representation_dump_department(None))
        self.assertEqual(
            normalize_representation_dump_department("media"),
            RepresentationDepartment.MEDIA,
        )
        self.assertEqual(
            normalize_representation_dump_department("Scheduling"),
            RepresentationDepartment.SCHEDULING,
        )

    def test_build_representation_dump_csv_includes_totals_and_mutations(self) -> None:
        # Arrange
        points_records = [
            RepresentationPoints(
                target_id=123,
                media_representation_points=2,
                scheduling_representation_points=3,
            ),
        ]
        mutations = [
            RepresentationPointMutation(
                id=7,
                target_id=123,
                changed_by_id=456,
                department=RepresentationDepartment.MEDIA,
                points_delta=2,
                reason="Coverage",
                created_at=datetime(2026, 6, 7, 10, 30, tzinfo=UTC),
            ),
        ]

        # Act
        csv_text = build_representation_dump_csv(points_records, mutations)

        # Assert
        self.assertIn("[POINT_TOTALS]", csv_text)
        self.assertIn("123,2,3,5", csv_text)
        self.assertIn("[MUTATIONS]", csv_text)
        self.assertIn("7,123,456,Media,2,Coverage,2026-06-07 10:30:00+00:00", csv_text)


if __name__ == "__main__":
    unittest.main()
