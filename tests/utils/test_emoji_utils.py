import unittest

from src.config.emojis import USNSOT_EMOJI
from src.config.ships import ROLE_ID_TITAN
from src.utils.emoji_utils import render_ship_label, resolve_ship_emoji


class TestEmojiUtils(unittest.TestCase):
    def test_resolve_ship_emoji_uses_ship_config(self) -> None:
        self.assertIn(":Titan:", resolve_ship_emoji(ship_role_id=ROLE_ID_TITAN))

    def test_resolve_ship_emoji_falls_back_to_configured_default(self) -> None:
        self.assertEqual(resolve_ship_emoji(ship_role_id=999999), USNSOT_EMOJI)

    def test_render_ship_label_uses_fallback_name_when_ship_unknown(self) -> None:
        self.assertEqual(
            render_ship_label(ship_role_id=999999),
            f"{USNSOT_EMOJI} Unknown ship",
        )
