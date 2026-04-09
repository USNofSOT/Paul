import unittest

from src.config.emojis import USNSOT_EMOJI
from src.config.ships import ROLE_ID_TITAN, ROLE_ID_VENOM
from src.notifications.admin.engineer_overview import build_ship_overview_field


class TestNotificationEngineerOverview(unittest.TestCase):
    def test_build_ship_overview_field_includes_ship_emojis(self) -> None:
        field = build_ship_overview_field(
            {
                ROLE_ID_TITAN: 2,
                ROLE_ID_VENOM: 1,
            }
        )

        self.assertIsNotNone(field)
        assert field is not None
        self.assertEqual(field.label, "Ship Overview")
        self.assertIn(":Titan:", field.value)
        self.assertIn(":Venom:", field.value)

    def test_build_ship_overview_field_uses_fallback_for_unknown_ship(self) -> None:
        field = build_ship_overview_field({999999: 3})

        self.assertIsNotNone(field)
        assert field is not None
        self.assertIn(USNSOT_EMOJI, field.value)
        self.assertIn("Unknown ship", field.value)
