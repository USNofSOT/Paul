from unittest import TestCase

from utils.ship_utils import get_auxiliary_ship_from_content, get_main_ship_from_content


class TestGetMainShipName(TestCase):

    def test_main_ship_included(self):
        content = "<@5848673888963>__**'s official log of the 134th voyage of the USS Phoenix , Auxiliary to the USS Platypus"
        self.assertEqual(get_main_ship_from_content(content), "USS Platypus")

    def test_main_ship_not_included(self):
        content = "<@5848673888963>__**'s official log of the 134th voyage of the USS Phoenix"
        self.assertEqual(get_main_ship_from_content(content), None)

    def test_main_ship_name(self):
        content = "<@5848673888963>__**'s official log of the 134th voyage of the USS Phoenix , Auxiliary to the USS Platypus**__ We started our adventure at Plunder"
        self.assertEqual(get_main_ship_from_content(content), "USS Platypus")

    def test_main_ship_name_with_emoji(self):
        content = "<@5848673888963>__**'s official log of the 134th voyage of the USS Phoenix , Auxiliary to the USS Platypus**__ We started our adventure at Plunder <:USS_Platypus:123456789>"
        self.assertEqual(get_main_ship_from_content(content), "USS Platypus")

    def test_main_ship_within_the_first_25_words(self):
        content = "We started our adventure at Plunder on the USS Phoenix, Auxiliary to the USS Platypus"
        self.assertEqual(get_main_ship_from_content(content), "USS Platypus")
        content = "We started our adventure at Plunder on the we dit a lot of yapping at least a good 25 words, so that is like more than 25 words. USS Phoenix"
        self.assertEqual(get_main_ship_from_content(content), None)

class TestGetAuxiliaryShipName(TestCase):

    def test_auxiliary_ship_included(self):
        content = "<@5848673888963>__**'s official log of the 134th voyage of the USS Phoenix , Auxiliary to the USS Platypus"
        self.assertEqual(get_auxiliary_ship_from_content(content), "USS Phoenix")

    def test_auxiliary_ship_not_included(self):
        content = "<@5848673888963>__**'s official log of the 134th voyage of the USS Adrestia"
        self.assertEqual(get_auxiliary_ship_from_content(content), None)

    def test_auxiliary_ship_name(self):
        content = "<@5848673888963>__**'s official log of the 134th voyage of the USS Phoenix , Auxiliary to the USS Platypus**__ We started our adventure at Plunder"
        self.assertEqual(get_auxiliary_ship_from_content(content), "USS Phoenix")

    def test_auxiliary_ship_name_with_emoji(self):
        content = "<@5848673888963>__**'s official log of the 134th voyage of the USS Phoenix , Auxiliary to the USS Platypus**__ We started our adventure at Plunder <:USS_Phoenix:123456789>"
        self.assertEqual(get_auxiliary_ship_from_content(content), "USS Phoenix")

    def test_auxiliary_ship_within_the_first_25_words(self):
        content = "We started our adventure at Plunder on the USS Phoenix, Auxiliary to the USS Platypus"
        self.assertEqual(get_auxiliary_ship_from_content(content), "USS Phoenix")
        content = "We started our adventure at Plunder on the USS Platypus we dit a lot of yapping at least a good 25 words, so that is like more than 25 words. USS Phoenix"
        self.assertEqual(get_auxiliary_ship_from_content(content), None)
