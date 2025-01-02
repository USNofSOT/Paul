import unittest
from lib2to3.fixes.fix_input import context

from utils.process_voyage_log import get_gold_count_from_content


class TestGetGoldCountFromContent(unittest.TestCase):
    def test_gold_at_beginning(self):
        content = "gold 100"
        self.assertEqual(get_gold_count_from_content(content), 100)

    def test_gold_with_colon(self):
        content = "gold: 1,000"
        self.assertEqual(get_gold_count_from_content(content), 1000)

    def test_gold_with_emoji(self):
        content = "<:Gold:965929014067867699> 10,000"
        self.assertEqual(get_gold_count_from_content(content), 10000)
        content = "<:gold:1323316150930636961> 10.000"
        self.assertEqual(get_gold_count_from_content(content), 10000)

    def test_gold_with_emoji_and_behind(self):
        content = "10,232 <:Gold:965929014067867699>"
        self.assertEqual(get_gold_count_from_content(content), 10232)
        content = "10.121 <:gold:1323316150930636961>"
        self.assertEqual(get_gold_count_from_content(content), 10121)

    def test_negative_gold(self):
        content = "gold -100"
        self.assertEqual(get_gold_count_from_content(content), 0)

    def test_max_20m_gold(self):
        content = "gold 20,000,001"
        self.assertEqual(get_gold_count_from_content(content), 20000000)

    def test_gold_both_sides(self):
        content = "<:gold:1323316150930636961> 10.010 <:gold:1323316150930636961>"
        self.assertEqual(get_gold_count_from_content(content), 10010)

    def test_weird_formatting(self):
        content = "Gold secured: 562.4123"
        self.assertEqual(get_gold_count_from_content(content), 5624123)

    def test_gold_at_end(self):
        content = "100 gold"
        self.assertEqual(get_gold_count_from_content(content), 100)

    def test_no_gold(self):
        content = "no gold here"
        self.assertEqual(get_gold_count_from_content(content), 0)

    def test_gold_with_text(self):
        content = "You have earned gold 2,500 today!"
        self.assertEqual(get_gold_count_from_content(content), 2500)

    def test_gold_with_extra_text(self):
        content = "Gold secured: 1,224,132"
        self.assertEqual(get_gold_count_from_content(content), 1224132)

