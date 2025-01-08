import unittest

from utils.process_voyage_log import (
    get_doubloon_count_from_content,
    get_gold_count_from_content,
)


class TestGetDoubloonCountFromContent(unittest.TestCase):
    def test_doubloons_at_beginning(self):
        content = "doubloons 100"
        self.assertEqual(get_doubloon_count_from_content(content), 100)

    def test_doubloons_with_colon(self):
        content = "doubloons: 1,000"
        self.assertEqual(get_doubloon_count_from_content(content), 1000)

    def test_doubloons_with_emoji(self):
        content = "<:Doubloons:965929014067867699> 10,000"
        self.assertEqual(get_doubloon_count_from_content(content), 10000)
        content = "<:doubloons:1323316150930636961> 10.000"
        self.assertEqual(get_doubloon_count_from_content(content), 10000)

    def test_doubloons_with_emoji_and_behind(self):
        content = "10,232 <:Doubloons:965929014067867699>"
        self.assertEqual(get_doubloon_count_from_content(content), 10232)
        content = "10.121 <:doubloons:1323316150930636961>"
        self.assertEqual(get_doubloon_count_from_content(content), 10121)

    def test_max_20m_doubloons(self):
        content = "doubloons 20,000,001"
        self.assertEqual(get_doubloon_count_from_content(content), 20000000)

    def test_doubloons_both_sides(self):
        content = "<:doubloons:1323316150930636961> 10.010 <:doubloons:1323316150930636961>"
        self.assertEqual(get_doubloon_count_from_content(content), 10010)

    def test_weird_formatting(self):
        content = "Doubloons secured: 562.4123"
        self.assertEqual(get_doubloon_count_from_content(content), 5624123)

    def test_doubloons_at_end(self):
        content = "122 doubloons"
        self.assertEqual(get_doubloon_count_from_content(content), 122)

    def test_no_doubloons(self):
        content = "no doubloons here"
        self.assertEqual(get_doubloon_count_from_content(content), 0)

    def test_doubloons_with_text(self):
        content = "You have earned doubloons 2,500 today!"
        self.assertEqual(get_doubloon_count_from_content(content), 2500)

    def test_doubloons_with_extra_text(self):
        content = "Doubloons secured: 1,224,132"
        self.assertEqual(get_doubloon_count_from_content(content), 1224132)

    def test_doubloons_with_previous_line_containing_numbers(self):
        content = "::Gold> Gold: 1536057\n:Doubloons> Doubloons: 12"
        self.assertEqual(get_doubloon_count_from_content(content), 12)

    def test_doubloons_with_emoji_named_doubloon(self):
        content = "::Gold> Gold: 1536057\n:Doubloon> 12"
        self.assertEqual(get_doubloon_count_from_content(content), 12)

    def test_doubloons_with_dash(self):
        content = "Doubloons - 234,646"
        self.assertEqual(get_doubloon_count_from_content(content), 234646)
        content = "548,646 - Doubloons"
        self.assertEqual(get_doubloon_count_from_content(content), 548646)

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

    def test_gold_with_space(self):
        content = "Gold 1 000"
        self.assertEqual(get_gold_count_from_content(content), 1000)
        content = "We as Gold Hoarders achieved so much, we even managed to sink a grade 3 reaper. \n \n Loot: \n 1 005 gold"
        self.assertEqual(get_gold_count_from_content(content), 1005)
        content = "212 543 gold"
        self.assertEqual(get_gold_count_from_content(content), 212543)

    def test_gold_and_number_earlier_in_log(self):
        content = "We voted up Gold hoarders proceeded to do a series of other things, like sinking a ship to then fight a grade 3 reaper, and then we did a fort. \n \n Loot: \n 1536057 gold"
        self.assertEqual(get_gold_count_from_content(content), 1536057)

    def test_gold_count_must_be_within_25_characters(self):
        twenty_five_characters = "Lorem ipsum dolor sit adi"
        content = "Gold " + twenty_five_characters + " 100"
        self.assertEqual(get_gold_count_from_content(content), 0)
        content = "Gold " + twenty_five_characters[1:] + " 100"
        self.assertEqual(get_gold_count_from_content(content), 100)

    def test_gold_count_with_dash(self):
        content = "Gold - 234,646"
        self.assertEqual(get_gold_count_from_content(content), 234646)
        content = "548,646 - Gold"
        self.assertEqual(get_gold_count_from_content(content), 548646)

