from unittest import TestCase

from data import VoyageType
from utils.ship_utils import (
    get_auxiliary_ship_from_content,
    get_count_from_content,
    get_main_ship_from_content,
    get_voyage_type_from_content,
)


class TestVoyageSpecification(TestCase):
    def test_valid_patrol(self):
        # Arrange
        content = "@Lt. Commander Terin Official Patrol Log of the 7th Voyage of the USS Grizzly, auxiliary to the USS Illustrious."
        # Act
        main_ship = get_main_ship_from_content(content)
        auxiliary_ship = get_auxiliary_ship_from_content(content)
        voyage_count = get_count_from_content(content)
        voyage_type = get_voyage_type_from_content(content)
        # Assert
        self.assertEqual(main_ship, "USS Illustrious")
        self.assertEqual(auxiliary_ship, "USS Grizzly")
        self.assertEqual(voyage_count, 7)
        self.assertEqual(voyage_type, VoyageType.PATROL)

    def test_valid_skirmish(self):
        # Arrange
        content = "@LCDR. Boats' Skirmish Log of the 62nd Voyage of the USS Adun"
        # Act
        main_ship = get_main_ship_from_content(content)
        auxiliary_ship = get_auxiliary_ship_from_content(content)
        voyage_count = get_count_from_content(content)
        voyage_type = get_voyage_type_from_content(content)
        # Assert
        self.assertEqual(main_ship, "USS Adun")
        self.assertEqual(auxiliary_ship, None)
        self.assertEqual(voyage_count, 62)
        self.assertEqual(voyage_type, VoyageType.SKIRMISH)

    def test_valid_convoy(self):
        # Arrange
        content = "@Colonel Neverband ‘s Log of the 120th deployment (Convoy) of the USS Illustrious"
        # Act
        main_ship = get_main_ship_from_content(content)
        auxiliary_ship = get_auxiliary_ship_from_content(content)
        voyage_count = get_count_from_content(content)
        voyage_type = get_voyage_type_from_content(content)
        # Assert
        self.assertEqual(main_ship, "USS Illustrious")
        self.assertEqual(auxiliary_ship, None)
        self.assertEqual(voyage_count, 120)
        self.assertEqual(voyage_type, VoyageType.CONVOY)

    def test_valid_adventure(self):
        # Arrange
        content = "@Petty Officer Marsh's Official Adventure Log of the 35th Official Voyage of the USS Thor, Auxiliary to the USS Audacious. 📜 🪶 "
        # Act
        main_ship = get_main_ship_from_content(content)
        auxiliary_ship = get_auxiliary_ship_from_content(content)
        voyage_count = get_count_from_content(content)
        voyage_type = get_voyage_type_from_content(content)
        # Assert
        self.assertEqual(main_ship, "USS Audacious")
        self.assertEqual(auxiliary_ship, "USS Thor")
        self.assertEqual(voyage_count, 35)
        self.assertEqual(voyage_type, VoyageType.ADVENTURE)

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

    def test_main_ship_with_dash_between_words(self):
        content = "We started our adventure at Plunder on the USS Phoenix, Auxiliary to the USS Platypus"
        self.assertEqual(get_main_ship_from_content(content), "USS Platypus")
        content = "We started our adventure at Plunder on the USS Phoenix, Auxiliary to the USS-Platypus"
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

    def test_auxiliary_ship_with_dash_between_words(self):
        content = "We started our adventure at Plunder on the USS Phoenix, Auxiliary to the USS Platypus"
        self.assertEqual(get_auxiliary_ship_from_content(content), "USS Phoenix")
        content = "We started our adventure at Plunder on the USS Phoenix, Auxiliary to the USS-Platypus"
        self.assertEqual(get_auxiliary_ship_from_content(content), None)