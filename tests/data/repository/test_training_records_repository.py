import unittest

from src.config.netc_server import (
    ALL_NETC_RECORDS_CHANNELS,
    COSA_GRADUATE_ROLE,
    COSA_INSTRUCTOR_ROLE,
    COSA_RECORDS_CHANNEL,
    LEGACY_NETC_RECORDS_CHANNELS,
    NETC_ACTIVE_CURRICULUMS,
    NETC_LEGACY_CURRICULUMS,
    NETC_RECORDS_CHANNELS,
    SLA_GRADUATE_ROLE,
    SLA_INSTRUCTOR_ROLE,
    SLA_RECORDS_CHANNEL,
    SNLA_GRADUATE_ROLE,
    SNLA_INSTRUCTOR_ROLE,
    SNLA_RECORDS_CHANNEL,
)
from src.config.training import ALL_TRAINING_RECORDS_CHANNELS
from src.data import TraingType, TrainingCategory
from src.data.repository.training_records_repository import (
    get_training_category_for_channel,
    get_training_type_for_channel,
    is_netc_records_channel,
)


class TestTrainingRecordsRepositoryConfiguration(unittest.TestCase):
    def test_new_active_curriculums_have_expected_channel_and_role_ids(self):
        self.assertEqual(SLA_RECORDS_CHANNEL, 1471663660060512487)
        self.assertEqual(SLA_INSTRUCTOR_ROLE, 1471675392023859200)
        self.assertEqual(SLA_GRADUATE_ROLE, 1471682430497984633)

        self.assertEqual(COSA_RECORDS_CHANNEL, 1471666458793873438)
        self.assertEqual(COSA_INSTRUCTOR_ROLE, 1471675547317964943)
        self.assertEqual(COSA_GRADUATE_ROLE, 1471682545883287757)

    def test_active_netc_channels_exclude_legacy_snla(self):
        self.assertIn(SLA_RECORDS_CHANNEL, NETC_RECORDS_CHANNELS)
        self.assertIn(COSA_RECORDS_CHANNEL, NETC_RECORDS_CHANNELS)
        self.assertNotIn(SNLA_RECORDS_CHANNEL, NETC_RECORDS_CHANNELS)
        self.assertEqual(LEGACY_NETC_RECORDS_CHANNELS, (SNLA_RECORDS_CHANNEL,))
        self.assertEqual(
            ALL_NETC_RECORDS_CHANNELS,
            NETC_RECORDS_CHANNELS + LEGACY_NETC_RECORDS_CHANNELS,
        )
        self.assertEqual(NETC_ACTIVE_CURRICULUMS[0][0], "JLA")
        self.assertEqual(
            NETC_LEGACY_CURRICULUMS,
            (("SNLA", SNLA_RECORDS_CHANNEL, SNLA_INSTRUCTOR_ROLE, SNLA_GRADUATE_ROLE),),
        )

    def test_all_training_channels_keep_legacy_snla_for_historical_handling(self):
        self.assertIn(SNLA_RECORDS_CHANNEL, ALL_TRAINING_RECORDS_CHANNELS)

    def test_netc_channel_classification_keeps_legacy_snla_accessible(self):
        expectations = (
            (SLA_RECORDS_CHANNEL, TraingType.SLA),
            (COSA_RECORDS_CHANNEL, TraingType.COSA),
            (SNLA_RECORDS_CHANNEL, TraingType.SNLA),
        )

        for channel_id, training_type in expectations:
            with self.subTest(channel_id=channel_id):
                self.assertTrue(is_netc_records_channel(channel_id))
                self.assertEqual(
                    get_training_category_for_channel(channel_id),
                    TrainingCategory.NETC,
                )
                self.assertEqual(
                    get_training_type_for_channel(channel_id),
                    training_type,
                )


if __name__ == "__main__":
    unittest.main()
