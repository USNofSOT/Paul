import unittest

from config.emojis import (
    ANCIENT_COINS_EMOJI,
    DOUBLOONS_ANIMATED_EMOJI,
    DOUBLOONS_EMOJI,
    GOLD_ANIMATED_EMOJI,
    GOLD_EMOJI,
)
from utils.process_voyage_log import (
    get_count_from_content_by_keyword,
    get_doubloon_count_from_content,
    get_gold_count_from_content,
)


class TestGetCountFromContentByKeyword(unittest.TestCase):
    def test_keyword_regular(self):
        # Arrange - content with its default keyword
        content = "doubloons 100"
        # Act
        result = get_count_from_content_by_keyword(content, "doubloons")
        # Assert
        self.assertEqual(result, 100)

    def test_keyword_alternative(self):
        # Arrange - content with a different keyword than the default
        content = "doubloon 200"
        # Act
        result = get_count_from_content_by_keyword(content, "doubloons")
        # Assert
        self.assertEqual(result, 200)

    def test_keyword_emoji(self):
        # Arrange - content with emojis
        content_doubloons = f"{DOUBLOONS_EMOJI} 100"
        content_doubloons_animated = f"{DOUBLOONS_ANIMATED_EMOJI} 200"
        content_gold = f"{GOLD_EMOJI} 300"
        content_gold_animated = f"{GOLD_ANIMATED_EMOJI} 400"
        content_ancient_coins = f"{ANCIENT_COINS_EMOJI} 500"
        content_fishes = "🐟 600"
        # Act
        result_doubloons = get_count_from_content_by_keyword(content_doubloons, "doubloons")
        result_doubloons_animated = get_count_from_content_by_keyword(content_doubloons_animated, "doubloons")
        result_gold = get_count_from_content_by_keyword(content_gold, "gold")
        result_gold_animated = get_count_from_content_by_keyword(content_gold_animated, "gold")
        result_ancient_coins = get_count_from_content_by_keyword(content_ancient_coins, "ancient coins")
        result_fishes = get_count_from_content_by_keyword(content_fishes, "fishes")
        # Assert
        self.assertEqual(result_doubloons, 100)
        self.assertEqual(result_doubloons_animated, 200)
        self.assertEqual(result_gold, 300)
        self.assertEqual(result_gold_animated, 400)
        self.assertEqual(result_ancient_coins, 500)
        self.assertEqual(result_fishes, 600)

    def test_keyword_with_more_text(self):
        # Arrange - content with more text in between the keyword and the count
        content = "doubloons confiscated: 300"
        # Act
        result = get_count_from_content_by_keyword(content, "doubloons")
        # Assert
        self.assertEqual(result, 300)

    def test_keyword_with_too_much_text(self):
        # Arrange - content with more than 25 characters between the keyword and the count
        content = "doubloons confiscated by the authorities: 400"
        # Act
        result = get_count_from_content_by_keyword(content, "doubloons")
        # Assert
        self.assertEqual(result, 0)

    def test_confiscated_amount_spaced(self):
        # Arrange - content with a space between the keyword and the count
        content = "gold 100 000"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 100000)

    def test_confiscated_amount_comma(self):
        # Arrange - content with a comma between the keyword and the count
        content = "gold 200,000"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 200000)

    def test_confiscated_amount_period(self):
        # Arrange - content with a period between the keyword and the count
        content = "gold 300.000"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 300000)

    def test_seperated_by_colon(self):
        # Arrange - content with a colon between the keyword and the count
        content = "gold: 400"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 400)

    def test_seperated_by_dash(self):
        # Arrange - content with a dash between the keyword and the count
        content = "gold - 500"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 500)

    def test_seperated_by_text(self):
        # Arrange - content with a text between the keyword and the count
        content = "gold confiscated 600"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 600)

    def test_seperated_by_too_much_text(self):
        # Arrange - content with a text between the keyword and the count
        content = "gold confiscated by the authorities 700"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 0)

    def test_markdown_bold(self):
        # Arrange - content with bold markdown
        content = "gold **800**"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 800)

    def test_markdown_numnber_italic_underline_bold(self):
        # Arrange - content with italic, underline, and bold markdown
        content_italic = "gold *900*"
        content_underline = "gold __1000__"
        content_bold = "gold **1100**"
        content_bold_underline = "gold __**1200**__"
        # Act
        result_italic = get_count_from_content_by_keyword(content_italic, "gold")
        result_underline = get_count_from_content_by_keyword(content_underline, "gold")
        result_bold = get_count_from_content_by_keyword(content_bold, "gold")
        result_bold_underline = get_count_from_content_by_keyword(content_bold_underline, "gold")
        # Assert
        self.assertEqual(result_italic, 900)
        self.assertEqual(result_underline, 1000)
        self.assertEqual(result_bold, 1100)
        self.assertEqual(result_bold_underline, 1200)

    def test_next_line(self):
        # Arrange - content with the count on the next line
        content = "gold\n800\ndoubloons\n900\nAncient Coins\n1000\nFishes\n1100"
        # Act
        result_gold = get_count_from_content_by_keyword(content, "gold")
        result_doubloons = get_count_from_content_by_keyword(content, "doubloons")
        result_ancient_coins = get_count_from_content_by_keyword(content, "ancient coins")
        result_fishes = get_count_from_content_by_keyword(content, "fishes")
        # Assert
        self.assertEqual(result_gold, 800)
        self.assertEqual(result_doubloons, 900)
        self.assertEqual(result_ancient_coins, 1000)
        self.assertEqual(result_fishes, 1100)

    def test_emojis_both_sides(self):
        # Arrange - content with emojis on both sides
        content = f"{DOUBLOONS_EMOJI} 100 {DOUBLOONS_EMOJI}"
        # Act
        result = get_count_from_content_by_keyword(content, "doubloons")
        # Assert
        self.assertEqual(result, 100)

    def test_fishes(self):
        # Arrange - content with the keyword "fishes"
        content_fishes = "fishes caught: 1200"
        content_fish = "fish caught: 1300"
        content_fish_emoji = "🐟 1400"
        # Act
        result_fishes = get_count_from_content_by_keyword(content_fishes, "fishes")
        result_fish = get_count_from_content_by_keyword(content_fish, "fishes")
        result_fish_emoji = get_count_from_content_by_keyword(content_fish_emoji, "fishes")
        # Assert
        self.assertEqual(result_fishes, 1200)
        self.assertEqual(result_fish, 1300)
        self.assertEqual(result_fish_emoji, 1400)

    def test_ignores_events(self):
        # Arrange - content with the keyword "events"
        content = "1x GH Dig :GoldHoarder: \n 1x Fort of the Damned :SkullOfDestiny: \n \n Gold : 20121"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 20121)

    def test_get_highest_cold_count(self):
        # Arrange - content with multiple gold counts
        content = "Gold 1,000\nGold 2,000\nGold 3,000"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")
        # Assert
        self.assertEqual(result, 3000)
        # Arrange - Add a higher gold count
        content += "\nGold 4,000"
        # Act
        result = get_count_from_content_by_keyword(content, "gold")

class TestGetDoubloonCountFromContent(unittest.TestCase):
    def test_doubloons_at_beginning(self):
        content = "doubloons 100"
        self.assertEqual(get_doubloon_count_from_content(content), 100)

    def test_doubloons_with_colon(self):
        content = "doubloons: 1,000"
        self.assertEqual(get_doubloon_count_from_content(content), 1000)

    def test_doubloons_with_emoji(self):
        content = f"{DOUBLOONS_EMOJI} 10,000"
        self.assertEqual(get_doubloon_count_from_content(content), 10000)
        content = f"{DOUBLOONS_EMOJI}  10.000"
        self.assertEqual(get_doubloon_count_from_content(content), 10000)

    # def test_doubloons_with_emoji_and_behind(self):
    #     content = "10,232 <:Doubloons:965929014067867699>"
    #     self.assertEqual(get_doubloon_count_from_content(content), 10232)
    #     content = "10.121 <:doubloons:1323316150930636961>"
    #     self.assertEqual(get_doubloon_count_from_content(content), 10121)

    def test_max_20m_doubloons(self):
        content = "doubloons 20,000,001"
        self.assertEqual(get_doubloon_count_from_content(content), 20000000)

    def test_doubloons_both_sides(self):
        content = f"{DOUBLOONS_EMOJI}  10.010 {DOUBLOONS_EMOJI}"
        self.assertEqual(get_doubloon_count_from_content(content), 10010)

    def test_weird_formatting(self):
        content = "Doubloons secured: 562.4123"
        self.assertEqual(get_doubloon_count_from_content(content), 5624123)

    # def test_doubloons_at_end(self):
    #     content = "122 doubloons"
    #     self.assertEqual(get_doubloon_count_from_content(content), 122)

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
        # content = "548,646 - Doubloons"
        # self.assertEqual(get_doubloon_count_from_content(content), 548646)

    def test_doubloons_with_italic_or_bold(self):
        content = "Doubloons **1,000**"
        self.assertEqual(get_doubloon_count_from_content(content), 1000)
        content = "Doubloons *1,000*"
        self.assertEqual(get_doubloon_count_from_content(content), 1000)

    def test_doubloons_with_underline(self):
        content = "Doubloons __1,050__"
        self.assertEqual(get_doubloon_count_from_content(content), 1050)

    def test_doubloons_with_bold_underline(self):
        content = "Doubloons __**1,055**__"
        self.assertEqual(get_doubloon_count_from_content(content), 1055)

# class TestGetGoldCountFromContent(unittest.TestCase):
#     def test_gold_at_beginning(self):
#         content = "gold 100"
#         self.assertEqual(get_gold_count_from_content(content), 100)

    def test_gold_with_colon(self):
        content = "gold: 1,000"
        self.assertEqual(get_gold_count_from_content(content), 1000)

    def test_gold_with_emoji(self):
        content = f"{GOLD_EMOJI} 10,000"
        self.assertEqual(get_gold_count_from_content(content), 10000)
        content = f"{GOLD_ANIMATED_EMOJI} 10.000"
        self.assertEqual(get_gold_count_from_content(content), 10000)

    # def test_gold_with_emoji_and_behind(self):
    #     content = "10,232 <:Gold:965929014067867699>"
    #     self.assertEqual(get_gold_count_from_content(content), 10232)
    #     content = "10.121 <:gold:1323316150930636961>"
    #     self.assertEqual(get_gold_count_from_content(content), 10121)

    def test_max_20m_gold(self):
        content = "gold 20,000,001"
        self.assertEqual(get_gold_count_from_content(content), 20000000)

    def test_gold_both_sides(self):
        content = f"{GOLD_EMOJI} 10.010 {GOLD_EMOJI}"
        self.assertEqual(get_gold_count_from_content(content), 10010)

    def test_weird_formatting(self):
        content = "Gold secured: 562.4123"
        self.assertEqual(get_gold_count_from_content(content), 5624123)

    # def test_gold_at_end(self):
    #     content = "100 gold"
    #     self.assertEqual(get_gold_count_from_content(content), 100)

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
        content = "We as Gold Hoarders achieved so much, we even managed to sink a grade 3 reaper. \n \n Loot gold: \n1 005 "
        self.assertEqual(get_gold_count_from_content(content), 1005)
        # content = "212 543 gold"
        # self.assertEqual(get_gold_count_from_content(content), 212543)

    def test_gold_and_number_earlier_in_log(self):
        content = "We voted up Gold hoarders proceeded to do a series of other things, like sinking a ship to then fight a grade 3 reaper, and then we did a fort. \n \n Loot gold: \n1536057 "
        self.assertEqual(get_gold_count_from_content(content), 1536057)
        content = "We voted up Gold hoarders 3 proceeded to do a series of other things, like sinking a ship to then fight a grade 3 reaper, and then we did a fort. \n \n Loot gold: \n1536057 "
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
        # content = "548,646 - Gold"
        # self.assertEqual(get_gold_count_from_content(content), 548646)

    def test_gold_count_with_italic_or_bold(self):
        content = "Gold **1,000**"
        self.assertEqual(get_gold_count_from_content(content), 1000)
        content = "Gold *1,000*"
        self.assertEqual(get_gold_count_from_content(content), 1000)

    def test_gold_count_with_underline(self):
        content = "Gold __1,050__"
        self.assertEqual(get_gold_count_from_content(content), 1050)

    def test_gold_count_with_bold_underline(self):
        content = "Gold __**1,055**__"
        self.assertEqual(get_gold_count_from_content(content), 1055)

