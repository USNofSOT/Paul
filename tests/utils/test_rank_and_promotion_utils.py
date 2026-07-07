import unittest
from types import SimpleNamespace

from src.utils.rank_and_promotion_utils import get_current_rank, get_current_rank_role_id


class TestRankAndPromotionUtils(unittest.TestCase):
    def test_get_current_rank_returns_none_for_missing_guild_member(self):
        self.assertIsNone(get_current_rank(None))

    def test_get_current_rank_returns_none_for_user_without_roles(self):
        user = SimpleNamespace(id=123)

        self.assertIsNone(get_current_rank(user))

    def test_get_current_rank_role_id_returns_none_for_missing_guild_member(self):
        self.assertIsNone(get_current_rank_role_id(None))

    def test_get_current_rank_role_id_returns_none_for_user_without_roles(self):
        user = SimpleNamespace(id=123)

        self.assertIsNone(get_current_rank_role_id(user))
