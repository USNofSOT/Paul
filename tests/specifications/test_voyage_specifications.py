import unittest

from utils.ship_utils import (
    get_auxiliary_ship_from_content,
    get_count_from_content,
    get_main_ship_from_content,
)


class TestVoyageSpecifications(unittest.TestCase):
    valid_specification_file = "voyage_specification.csv"

    def setUp(self):
        self.test_cases = []
        with open(self.valid_specification_file, "r") as f:
            for line in f:
                if not line.startswith("#"):
                    self.test_cases.append(line.strip().split(";"))

    def test_voyage_specifications_count(self):
        for test_case in self.test_cases[1:]:
            content, ship_voyage_count, _, _, _ = test_case
            self.assertEqual(get_count_from_content(content), int(ship_voyage_count))

    def test_voyage_specifications_auxiliary_ship(self):
        for test_case in self.test_cases[1:]:
            content, _, _, auxiliary_ship, _ = test_case
            auxiliary_ship = auxiliary_ship if auxiliary_ship != "None" else None
            self.assertEqual(get_auxiliary_ship_from_content(content), auxiliary_ship)

    def test_voyage_specifications_main_ship(self):
        for test_case in self.test_cases[1:]:
            content, _, _, _, main_ship = test_case
            main_ship = main_ship if main_ship != "None" else None
            self.assertEqual(get_main_ship_from_content(content), main_ship)
