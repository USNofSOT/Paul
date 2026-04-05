import unittest
from types import SimpleNamespace

from src.cogs.commands.JE.training_records import (
    ACTIVE_NETC_POINT_FIELDS,
    LEGACY_TRAINING_POINT_FIELDS,
    _curricula_for_graduate_roles,
    _curricula_for_instructor_roles,
    _format_curriculum_list,
    _get_positive_point_fields,
)
from src.config.netc_server import NETC_ACTIVE_CURRICULUMS, NETC_LEGACY_CURRICULUMS


class TestTrainingRecordsHelpers(unittest.TestCase):
    def test_curricula_helpers_split_active_and_legacy_roles(self) -> None:
        member_role_ids = {
            NETC_ACTIVE_CURRICULUMS[0][2],
            NETC_ACTIVE_CURRICULUMS[1][3],
            NETC_LEGACY_CURRICULUMS[0][2],
            NETC_LEGACY_CURRICULUMS[0][3],
        }

        self.assertEqual(
            _curricula_for_instructor_roles(member_role_ids, NETC_ACTIVE_CURRICULUMS),
            ["JLA"],
        )
        self.assertEqual(
            _curricula_for_graduate_roles(member_role_ids, NETC_ACTIVE_CURRICULUMS),
            ["SLA"],
        )
        self.assertEqual(
            _curricula_for_instructor_roles(member_role_ids, NETC_LEGACY_CURRICULUMS),
            ["SNLA"],
        )
        self.assertEqual(
            _curricula_for_graduate_roles(member_role_ids, NETC_LEGACY_CURRICULUMS),
            ["SNLA"],
        )
        self.assertEqual(_format_curriculum_list(["SNLA"]), "- SNLA")

    def test_point_fields_keep_legacy_stats_separate(self) -> None:
        training_record = SimpleNamespace(
            jla_training_points=4,
            sla_training_points=3,
            cosa_training_points=0,
            ocs_training_points=1,
            socs_training_points=0,
            snla_training_points=2,
            nla_training_points=5,
            vla_training_points=0,
        )

        self.assertEqual(
            _get_positive_point_fields(training_record, ACTIVE_NETC_POINT_FIELDS),
            [
                ("Total JLA Points", 4),
                ("Total SLA Points", 3),
                ("Total OCS Points", 1),
            ],
        )
        self.assertEqual(
            _get_positive_point_fields(training_record, LEGACY_TRAINING_POINT_FIELDS),
            [
                ("Total SNLA Points", 2),
                ("Total NLA Points", 5),
            ],
        )


if __name__ == "__main__":
    unittest.main()
